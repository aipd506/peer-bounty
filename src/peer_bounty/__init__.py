"""
peer-bounty: Zero-backend peer-to-peer Bitcoin bounty badges for GitHub issues.
"""

__version__ = "0.1.0"
__author__ = "aipd506"

from .badge import generate_svg_badge, generate_markdown_badge
from .issue_parser import parse_pr_for_bounty, extract_payout_address
from .state import BountyLedger, BountyRecord
from .settlement import resolve_lightning_address, verify_payment_preimage

__all__ = [
    "generate_svg_badge",
    "generate_markdown_badge",
    "parse_pr_for_bounty",
    "extract_payout_address",
    "BountyLedger",
    "BountyRecord",
    "resolve_lightning_address",
    "verify_payment_preimage",
    "__version__"
]
