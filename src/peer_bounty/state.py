"""
Tamper-evident ledger management and receipt verification for Peer-Bounty.
Maintains state in a local or git-committed ledger file with cryptographic checksums.
"""
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

def compute_receipt_hash(
    repo: str,
    issue_number: int,
    sats: int,
    recipient: str,
    preimage: str,
    settled_at: str
) -> str:
    """
    Computes a cryptographic SHA-256 receipt digest binding the repository, issue,
    amount, recipient, settlement timestamp, and Lightning payment preimage.
    """
    canonical_str = f"{repo}|{issue_number}|{sats}|{recipient}|{preimage}|{settled_at}"
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

class BountyRecord:
    def __init__(
        self,
        issue_number: int,
        sats: int,
        status: str = "open",
        created_at: Optional[str] = None,
        settled_at: Optional[str] = None,
        settled_pr: Optional[int] = None,
        recipient: Optional[str] = None,
        preimage: Optional[str] = None,
        receipt_hash: Optional[str] = None
    ):
        self.issue_number = issue_number
        self.sats = sats
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.settled_at = settled_at
        self.settled_pr = settled_pr
        self.recipient = recipient
        self.preimage = preimage
        self.receipt_hash = receipt_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_number": self.issue_number,
            "sats": self.sats,
            "status": self.status,
            "created_at": self.created_at,
            "settled_at": self.settled_at,
            "settled_pr": self.settled_pr,
            "recipient": self.recipient,
            "preimage": self.preimage,
            "receipt_hash": self.receipt_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BountyRecord":
        return cls(
            issue_number=data["issue_number"],
            sats=data["sats"],
            status=data.get("status", "open"),
            created_at=data.get("created_at"),
            settled_at=data.get("settled_at"),
            settled_pr=data.get("settled_pr"),
            recipient=data.get("recipient"),
            preimage=data.get("preimage"),
            receipt_hash=data.get("receipt_hash")
        )

class BountyLedger:
    def __init__(self, filepath: str, repo: str = "local/repo"):
        self.filepath = filepath
        self.repo = repo
        self.bounties: Dict[int, BountyRecord] = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.repo = data.get("repo", self.repo)
                    raw_bounties = data.get("bounties", {})
                    self.bounties = {
                        int(k): BountyRecord.from_dict(v) for k, v in raw_bounties.items()
                    }
            except Exception:
                self.bounties = {}
        else:
            self.bounties = {}

    def save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
        data = {
            "version": "1.0",
            "repo": self.repo,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "bounties": {
                str(k): v.to_dict() for k, v in self.bounties.items()
            }
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register_bounty(self, issue_number: int, sats: int) -> BountyRecord:
        if issue_number in self.bounties:
            existing = self.bounties[issue_number]
            if existing.status == "settled":
                raise ValueError(f"Issue #{issue_number} has already been settled and closed.")
            existing.sats = sats
            existing.status = "open"
            self.save()
            return existing

        record = BountyRecord(issue_number=issue_number, sats=sats, status="open")
        self.bounties[issue_number] = record
        self.save()
        return record

    def settle_bounty(
        self,
        issue_number: int,
        pr_number: int,
        recipient: str,
        preimage: str
    ) -> BountyRecord:
        if issue_number not in self.bounties:
            raise KeyError(f"Issue #{issue_number} is not registered in the bounty ledger.")

        record = self.bounties[issue_number]
        if record.status == "settled":
            raise ValueError(f"Issue #{issue_number} is already settled.")

        settled_at = datetime.now(timezone.utc).isoformat()
        receipt = compute_receipt_hash(
            repo=self.repo,
            issue_number=issue_number,
            sats=record.sats,
            recipient=recipient,
            preimage=preimage,
            settled_at=settled_at
        )

        record.status = "settled"
        record.settled_at = settled_at
        record.settled_pr = pr_number
        record.recipient = recipient
        record.preimage = preimage
        record.receipt_hash = receipt

        self.save()
        return record

    def verify_record(self, issue_number: int) -> bool:
        if issue_number not in self.bounties:
            return False
        rec = self.bounties[issue_number]
        if rec.status != "settled" or not rec.receipt_hash:
            return True
        computed = compute_receipt_hash(
            repo=self.repo,
            issue_number=issue_number,
            sats=rec.sats,
            recipient=rec.recipient or "",
            preimage=rec.preimage or "",
            settled_at=rec.settled_at or ""
        )
        return computed == rec.receipt_hash
