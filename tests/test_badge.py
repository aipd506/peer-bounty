"""
Unit tests for badge generation module.
"""
import unittest
from peer_bounty.badge import generate_svg_badge, generate_markdown_badge

class TestBadge(unittest.TestCase):
    def test_generate_svg_open_status(self):
        svg = generate_svg_badge(sats=25000, status="open")
        self.assertIn("<svg", svg)
        self.assertIn("25,000 sats", svg)
        self.assertIn("#f7931a", svg)  # Bitcoin Orange

    def test_generate_svg_settled_status(self):
        svg = generate_svg_badge(sats=50000, status="settled")
        self.assertIn("50,000 sats [settled]", svg)
        self.assertIn("#2da44e", svg)  # Verified Green

    def test_generate_markdown_badge(self):
        md = generate_markdown_badge(issue_number=42, sats=100000, repo="aipd506/peer-bounty")
        self.assertIn("Bitcoin Bounty: 100,000 sats", md)
        self.assertIn("https://raw.githubusercontent.com/aipd506/peer-bounty/main/.peer-bounty/badges/issue-42.svg", md)
        self.assertIn("https://github.com/aipd506/peer-bounty/issues/42", md)

if __name__ == "__main__":
    unittest.main()
