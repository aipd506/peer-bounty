"""
Lightning settlement and LNURL resolution engine for Peer-Bounty.
Handles Lightning address lookups, invoice generation, preimage verification,
and GitHub settlement comment formatting.
"""
import json
import hashlib
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple

def resolve_lightning_address(lightning_address: str, sats: int) -> Tuple[bool, Dict[str, Any]]:
    """
    Resolves an LNURL-pay address (username@domain.com) into a payable Lightning invoice.
    """
    if "@" not in lightning_address:
        return False, {"error": "Invalid Lightning address format. Expected username@domain.com"}

    username, domain = lightning_address.split("@", 1)
    url = f"https://{domain}/.well-known/lnurlp/{username}"

    headers = {"User-Agent": "Peer-Bounty/0.1.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") == "ERROR":
            return False, {"error": data.get("reason", "LNURL endpoint returned error")}

        callback_url = data.get("callback")
        min_sendable = data.get("minSendable", 1000)  # in millisats
        max_sendable = data.get("maxSendable", 100000000000)

        millisats = sats * 1000
        if millisats < min_sendable or millisats > max_sendable:
            return False, {
                "error": f"Amount {sats} sats is outside allowable bounds ({min_sendable // 1000} - {max_sendable // 1000} sats)"
            }

        # Request payment invoice from callback
        sep = "&" if "?" in callback_url else "?"
        invoice_req_url = f"{callback_url}{sep}amount={millisats}"
        inv_req = urllib.request.Request(invoice_req_url, headers=headers)
        with urllib.request.urlopen(inv_req, timeout=10) as inv_resp:
            inv_data = json.loads(inv_resp.read().decode("utf-8"))

        pr = inv_data.get("pr")
        if not pr:
            return False, {"error": "No payment request (pr) returned by Lightning service"}

        return True, {
            "invoice": pr,
            "recipient": lightning_address,
            "sats": sats
        }
    except Exception as e:
        return False, {"error": f"Failed to connect to Lightning address host: {str(e)}"}

def verify_payment_preimage(payment_hash: str, preimage: str) -> bool:
    """
    Verifies that SHA256(preimage) matches the target payment hash.
    Preimage and payment_hash can be provided in hex or byte format.
    """
    try:
        clean_preimage = preimage.replace("0x", "").strip()
        clean_hash = payment_hash.replace("0x", "").strip()

        preimage_bytes = bytes.fromhex(clean_preimage)
        computed_hash = hashlib.sha256(preimage_bytes).hexdigest()

        return computed_hash.lower() == clean_hash.lower()
    except Exception:
        return False

def format_settlement_comment(
    issue_number: int,
    pr_number: int,
    sats: int,
    recipient: str,
    preimage: str,
    receipt_hash: str,
    settled_at: str
) -> str:
    """
    Generates a standardized, transparent GitHub issue comment acknowledging settlement.
    """
    return (
        f"### Peer-Bounty Settlement Confirmation\n\n"
        f"Pull request #{pr_number} successfully resolved issue #{issue_number} and has been merged by a repository maintainer.\n\n"
        f"1. Settled Amount: {sats:,} satoshis\n"
        f"2. Recipient Address: `{recipient}`\n"
        f"3. Payment Preimage: `{preimage}`\n"
        f"4. Cryptographic Receipt Hash: `{receipt_hash}`\n"
        f"5. Settlement Timestamp: `{settled_at}`\n\n"
        f"*Settled autonomously by [Peer-Bounty](https://github.com/aipd506/peer-bounty). Zero platform fees deducted.*"
    )
