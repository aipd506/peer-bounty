"""
Unit tests for settlement verification and comment formatting.
"""
import hashlib
import unittest
from peer_bounty.settlement import verify_payment_preimage, format_settlement_comment

class TestSettlement(unittest.TestCase):
    def test_verify_payment_preimage(self):
        secret = b"correct_payment_preimage_32_bytes"
        expected_hash = hashlib.sha256(secret).hexdigest()
        preimage_hex = secret.hex()

        self.assertTrue(verify_payment_preimage(expected_hash, preimage_hex))
        self.assertFalse(verify_payment_preimage(expected_hash, "001122334455"))

    def test_format_settlement_comment(self):
        comment = format_settlement_comment(
            issue_number=42,
            pr_number=105,
            sats=50000,
            recipient="alice@getalby.com",
            preimage="abc123preimage",
            receipt_hash="0xdeadbeef",
            settled_at="2026-10-11T12:00:00Z"
        )
        self.assertIn("Pull request #105 successfully resolved issue #42", comment)
        self.assertIn("50,000 satoshis", comment)
        self.assertIn("alice@getalby.com", comment)
        self.assertIn("abc123preimage", comment)

if __name__ == "__main__":
    unittest.main()
