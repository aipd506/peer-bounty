"""
Unit tests for Peer-Bounty CLI subcommands.
"""
import io
import os
import unittest
from unittest.mock import patch
import tempfile
from peer_bounty.cli import main

class TestCli(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ledger_file = os.path.join(self.temp_dir.name, "bounties.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_version(self):
        with io.StringIO() as buf, patch("sys.stdout", buf):
            with self.assertRaises(SystemExit) as cm:
                main(["--version"])
            self.assertEqual(cm.exception.code, 0)

    def test_cli_badge_generation(self):
        output_svg = os.path.join(self.temp_dir.name, "badge.svg")
        with io.StringIO() as buf, patch("sys.stdout", buf):
            ret = main([
                "badge",
                "--issue", "42",
                "--sats", "25000",
                "--repo", "aipd506/peer-bounty",
                "--output", output_svg
            ])
            self.assertEqual(ret, 0)
            self.assertTrue(os.path.exists(output_svg))

    def test_cli_check_pr(self):
        with io.StringIO() as buf, patch("sys.stdout", buf):
            ret = main([
                "check-pr",
                "--title", "feat: close #42",
                "--body", "Lightning-Address: alice@getalby.com"
            ])
            self.assertEqual(ret, 0)
            out = buf.getvalue()
            self.assertIn("alice@getalby.com", out)
            self.assertIn("42", out)

    def test_cli_settle_and_verify(self):
        with io.StringIO() as buf, patch("sys.stdout", buf):
            ret_settle = main([
                "settle",
                "--issue", "99",
                "--pr", "101",
                "--recipient", "bob@stacker.news",
                "--sats", "50000",
                "--preimage", "0123456789abcdef",
                "--ledger", self.ledger_file
            ])
            self.assertEqual(ret_settle, 0)

        with io.StringIO() as buf, patch("sys.stdout", buf):
            ret_verify = main([
                "verify-receipt",
                "--issue", "99",
                "--ledger", self.ledger_file
            ])
            self.assertEqual(ret_verify, 0)
            self.assertIn("cryptographically valid", buf.getvalue())

if __name__ == "__main__":
    unittest.main()
