"""
Pull request and issue parser for Peer-Bounty.
Extracts linked closing issue numbers and recipient payout coordinates.
"""
import re
from typing import List, Optional, Dict, Any

# Matches standard GitHub issue closing keywords (Closes #123, Fixes issue #456, Resolves #789)
CLOSING_KEYWORD_REGEX = re.compile(
    r"\b(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)(?:\s+issue)?\s+#(\d+)\b",
    re.IGNORECASE
)

# Matches lightning addresses (alice@domain.com) and LNURL strings
LIGHTNING_ADDRESS_REGEX = re.compile(
    r"\b(?:lightning-address|lightning|ln-address|lnurl):\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b",
    re.IGNORECASE
)

# Matches Bitcoin Native SegWit (Bech32 bc1q...) and Taproot (bc1p...) addresses
BITCOIN_ADDRESS_REGEX = re.compile(
    r"\b(?:btc-address|bitcoin-address|bitcoin|btc):\s*(bc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{38,90})\b",
    re.IGNORECASE
)

def extract_linked_issues(text: str) -> List[int]:
    """
    Extracts all distinct issue numbers targeted for closure in a PR title, body, or commit text.
    """
    if not text:
        return []
    matches = CLOSING_KEYWORD_REGEX.findall(text)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for m in matches:
        num = int(m)
        if num not in seen:
            seen.add(num)
            result.append(num)
    return result

def extract_payout_address(text: str) -> Dict[str, Optional[str]]:
    """
    Extracts explicit Lightning or Bitcoin Layer 1 payout coordinates from PR text or commit trailers.
    """
    if not text:
        return {"lightning": None, "bitcoin": None}

    ln_match = LIGHTNING_ADDRESS_REGEX.search(text)
    btc_match = BITCOIN_ADDRESS_REGEX.search(text)

    # Fallback: scan for standalone valid email-like Lightning addresses on dedicated lines
    lightning_addr = ln_match.group(1).strip() if ln_match else None
    if not lightning_addr:
        standalone_ln = re.search(r"^\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\s*$", text, re.MULTILINE)
        if standalone_ln and ("@" in standalone_ln.group(1)):
            candidate = standalone_ln.group(1).strip()
            # Verify candidate has common LN domain or username structure
            if any(dom in candidate.lower() for dom in ["getalby.com", "stacker.news", "blink.sv", "coinos.io", "walletofsatoshi.com", "vitor.net"]):
                lightning_addr = candidate

    bitcoin_addr = btc_match.group(1).strip() if btc_match else None

    return {
        "lightning": lightning_addr,
        "bitcoin": bitcoin_addr
    }

def parse_pr_for_bounty(pr_title: str, pr_body: str, commit_messages: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Comprehensive parse of a pull request for bounty closure targets and payout addresses.
    """
    full_text = f"{pr_title}\n\n{pr_body}"
    if commit_messages:
        full_text += "\n\n" + "\n".join(commit_messages)

    linked_issues = extract_linked_issues(full_text)
    payout = extract_payout_address(full_text)

    return {
        "linked_issues": linked_issues,
        "recipient_lightning": payout["lightning"],
        "recipient_bitcoin": payout["bitcoin"],
        "has_payout_target": bool(payout["lightning"] or payout["bitcoin"])
    }
