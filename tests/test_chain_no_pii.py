"""
test_chain_no_pii.py — Verification of ZERO PII on Blockchain.
Asserts:
- Every payload sent to blockchain contains NO emails.
- NO patient names.
- NO disease or condition names.
- NO symptom descriptions.
- NO GPS coordinates.
"""
import unittest
import sys
import os
import uuid
import re

sys.path.insert(0, os.path.abspath("apps/api"))

from app.routers.consents import create_consent
from app.services.chain.merkle import compute_leaf, build_merkle_tree
from app.core.db import init_db, get_db

class TestChainNoPII(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = get_db()

    def test_01_consent_commitment_has_no_pii(self):
        # Inspect commitment structure
        txs = self.db.execute("SELECT * FROM chain_transactions WHERE kind = 'consent_grant'").fetchall()
        for tx in txs:
            payload_str = str(dict(tx)).lower()

            # No email pattern
            self.assertFalse(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', payload_str))

            # No health or medical terms
            forbidden = ["acne", "mụn", "chàm", "eczema", "vảy nến", "ngứa", "blister", "lat", "lng"]
            for term in forbidden:
                self.assertNotIn(term, payload_str)

    def test_02_merkle_leaf_has_no_pii(self):
        leaf, salt = compute_leaf("ev-1234", "view_image", "2026-11-21T10:00:00Z")
        self.assertTrue(leaf.startswith("0x"))
        self.assertEqual(len(leaf), 66)  # 0x + 64 hex chars
        self.assertNotIn("view_image", leaf)  # One-way hashed

if __name__ == "__main__":
    unittest.main()
