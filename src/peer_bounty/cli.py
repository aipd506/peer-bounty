"""
Command-line interface for Peer-Bounty.
"""
import sys
import os
import json
import argparse
from typing import List, Optional
from .badge import generate_svg_badge, generate_markdown_badge
from .issue_parser import parse_pr_for_bounty
from .state import BountyLedger, compute_receipt_hash
from .settlement import format_settlement_comment, verify_payment_preimage
from . import __version__

WORKFLOW_TEMPLATE = """name: Peer-Bounty Settlement

on:
  pull_request:
    types: [closed]

jobs:
  settle:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Peer-Bounty
        run: pip install peer-bounty

      - name: Evaluate and Settle Bounty
        env:
          PR_TITLE: ${{ github.event.pull_request.title }}
          PR_BODY: ${{ github.event.pull_request.body }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NWC_SECRET: ${{ secrets.NWC_SECRET }}
        run: |
          peerbounty action-settle
"""

def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="peerbounty",
        description="Zero-backend peer-to-peer Bitcoin bounty badges for GitHub issues."
    )
    parser.add_argument("--version", action="version", version=f"peer-bounty {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

    # 1. init
    init_parser = subparsers.add_parser("init", help="Initialize Peer-Bounty workflow in the current repository")

    # 2. badge
    badge_parser = subparsers.add_parser("badge", help="Generate SVG badge and markdown snippet for an issue")
    badge_parser.add_argument("--issue", type=int, required=True, help="GitHub issue number")
    badge_parser.add_argument("--sats", type=int, required=True, help="Bounty amount in satoshis")
    badge_parser.add_argument("--status", type=str, default="open", choices=["open", "funded", "settled", "closed"], help="Badge status")
    badge_parser.add_argument("--repo", type=str, default="owner/repo", help="Target GitHub repository (owner/name)")
    badge_parser.add_argument("--output", type=str, help="Optional output filepath for SVG badge")

    # 3. check-pr
    check_parser = subparsers.add_parser("check-pr", help="Parse a pull request for linked issues and payout targets")
    check_parser.add_argument("--title", type=str, default="", help="PR title")
    check_parser.add_argument("--body", type=str, default="", help="PR description body")

    # 4. settle
    settle_parser = subparsers.add_parser("settle", help="Record and settle a bounty for an issue")
    settle_parser.add_argument("--issue", type=int, required=True, help="Issue number to settle")
    settle_parser.add_argument("--pr", type=int, required=True, help="Closing PR number")
    settle_parser.add_argument("--recipient", type=str, required=True, help="Recipient Lightning address or Bitcoin address")
    settle_parser.add_argument("--sats", type=int, default=50000, help="Satoshi amount (if registering new)")
    settle_parser.add_argument("--preimage", type=str, default="simulated_settlement_preimage", help="Lightning payment preimage")
    settle_parser.add_argument("--ledger", type=str, default=".peer-bounty/bounties.json", help="Path to ledger file")
    settle_parser.add_argument("--repo", type=str, default="owner/repo", help="GitHub repo name")

    # 5. verify-receipt
    verify_parser = subparsers.add_parser("verify-receipt", help="Verify cryptographic integrity of an issue settlement")
    verify_parser.add_argument("--issue", type=int, required=True, help="Issue number to verify")
    verify_parser.add_argument("--ledger", type=str, default=".peer-bounty/bounties.json", help="Path to ledger file")

    args = parser.parse_args(argv)

    if args.subcommand == "init":
        workflow_dir = os.path.join(".github", "workflows")
        os.makedirs(workflow_dir, exist_ok=True)
        workflow_path = os.path.join(workflow_dir, "peer-bounty.yml")
        with open(workflow_path, "w", encoding="utf-8") as f:
            f.write(WORKFLOW_TEMPLATE)
        os.makedirs(".peer-bounty", exist_ok=True)
        print(f"[+] Initialized Peer-Bounty workflow at {workflow_path}")
        return 0

    elif args.subcommand == "badge":
        svg = generate_svg_badge(sats=args.sats, status=args.status)
        md = generate_markdown_badge(issue_number=args.issue, sats=args.sats, repo=args.repo, status=args.status)
        if args.output:
            out_dir = os.path.dirname(os.path.abspath(args.output))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"[+] Saved SVG badge to {args.output}")
        print("\nMarkdown Snippet:")
        print(md)
        return 0

    elif args.subcommand == "check-pr":
        result = parse_pr_for_bounty(pr_title=args.title, pr_body=args.body)
        print(json.dumps(result, indent=2))
        return 0

    elif args.subcommand == "settle":
        ledger = BountyLedger(filepath=args.ledger, repo=args.repo)
        if args.issue not in ledger.bounties:
            ledger.register_bounty(issue_number=args.issue, sats=args.sats)

        rec = ledger.settle_bounty(
            issue_number=args.issue,
            pr_number=args.pr,
            recipient=args.recipient,
            preimage=args.preimage
        )
        comment = format_settlement_comment(
            issue_number=args.issue,
            pr_number=args.pr,
            sats=rec.sats,
            recipient=args.recipient,
            preimage=args.preimage,
            receipt_hash=rec.receipt_hash or "",
            settled_at=rec.settled_at or ""
        )
        print(f"[+] Successfully settled issue #{args.issue} for {rec.sats:,} sats!")
        print("\nSettlement Comment:")
        print(comment)
        return 0

    elif args.subcommand == "verify-receipt":
        ledger = BountyLedger(filepath=args.ledger)
        is_valid = ledger.verify_record(issue_number=args.issue)
        if is_valid:
            print(f"[+] Issue #{args.issue} receipt is cryptographically valid and untampered.")
            return 0
        else:
            print(f"[!] Issue #{args.issue} receipt verification failed or hash mismatch!")
            return 1

    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
