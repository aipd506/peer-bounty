"""
Unit tests for issue parser and payout coordinate extraction.
"""
import unittest
from peer_bounty.issue_parser import extract_linked_issues, extract_payout_address, parse_pr_for_bounty

class TestIssueParser(unittest.TestCase):
    def test_extract_linked_issues(self):
        text = """
This pull request resolves issue #105 and also fixes #106.
Supercedes old approach from closes #42.
"""
        issues = extract_linked_issues(text)
        self.assertEqual(issues, [105, 106, 42])

    def test_extract_lightning_address(self):
        body = "Implemented core feature.\n\nLightning-Address: alice@getalby.com"
        res = extract_payout_address(body)
        self.assertEqual(res["lightning"], "alice@getalby.com")

    def test_extract_bitcoin_address(self):
        body = "Bug fixed in calculation.\n\nBtc-Address: bc1qaedjdrkrhjya767yvfz676jeyx5an04kfwzczg"
        res = extract_payout_address(body)
        self.assertEqual(res["bitcoin"], "bc1qaedjdrkrhjya767yvfz676jeyx5an04kfwzczg")

    def test_parse_pr_for_bounty_end_to_end(self):
        title = "feat: add multi-currency exchange rates"
        body = """
Closes #25.

Fully implemented with unit tests.
Lightning: satoshi@stacker.news
"""
        parsed = parse_pr_for_bounty(title, body)
        self.assertEqual(parsed["linked_issues"], [25])
        self.assertEqual(parsed["recipient_lightning"], "satoshi@stacker.news")
        self.assertTrue(parsed["has_payout_target"])

if __name__ == "__main__":
    unittest.main()
