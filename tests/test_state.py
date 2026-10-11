"""
Unit tests for tamper-evident ledger and cryptographic receipt verification.
"""
import os
import unittest
import tempfile
from peer_bounty.state import BountyLedger, compute_receipt_hash

class TestState(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ledger_file = os.path.join(self.temp_dir.name, "bounties.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_and_persist_bounty(self):
        ledger = BountyLedger(filepath=self.ledger_file, repo="owner/repo")
        rec = ledger.register_bounty(issue_number=10, sats=50000)
        self.assertEqual(rec.issue_number, 10)
        self.assertEqual(rec.sats, 50000)
        self.assertEqual(rec.status, "open")

        # Reload from disk
        ledger2 = BountyLedger(filepath=self.ledger_file, repo="owner/repo")
        self.assertIn(10, ledger2.bounties)
        self.assertEqual(ledger2.bounties[10].sats, 50000)

    def test_settle_bounty_and_verify_receipt(self):
        ledger = BountyLedger(filepath=self.ledger_file, repo="owner/repo")
        ledger.register_bounty(issue_number=20, sats=75000)

        preimage = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        rec = ledger.settle_bounty(
            issue_number=20,
            pr_number=5,
            recipient="alice@getalby.com",
            preimage=preimage
        )
        self.assertEqual(rec.status, "settled")
        self.assertEqual(rec.settled_pr, 5)
        self.assertTrue(rec.receipt_hash)

        # Verification must pass
        self.assertTrue(ledger.verify_record(issue_number=20))

    def test_prevent_double_settlement(self):
        ledger = BountyLedger(filepath=self.ledger_file, repo="owner/repo")
        ledger.register_bounty(issue_number=30, sats=10000)
        ledger.settle_bounty(
            issue_number=30,
            pr_number=8,
            recipient="bob@domain.com",
            preimage="preimage_a"
        )

        with self.assertRaises(ValueError):
            ledger.settle_bounty(
                issue_number=30,
                pr_number=9,
                recipient="eve@domain.com",
                preimage="preimage_b"
            )

    def test_detect_tampering(self):
        ledger = BountyLedger(filepath=self.ledger_file, repo="owner/repo")
        ledger.register_bounty(issue_number=40, sats=20000)
        ledger.settle_bounty(
            issue_number=40,
            pr_number=12,
            recipient="charlie@domain.com",
            preimage="valid_preimage"
        )
        self.assertTrue(ledger.verify_record(issue_number=40))

        # Maliciously modify recipient or sats
        ledger.bounties[40].sats = 999999
        self.assertFalse(ledger.verify_record(issue_number=40))

if __name__ == "__main__":
    unittest.main()
