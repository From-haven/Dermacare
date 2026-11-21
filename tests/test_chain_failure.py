"""
test_chain_failure.py — T10: Blockchain Transaction Failure and Status Isolation.
Asserts:
- Failed blockchain transaction reports FAILED or pending.
- NEVER reports success when receipt status != 1 (T10).
- Partner package is NOT activated if transaction fails.
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.services.clinics import purchase_partner_package

class TestChainFailure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = get_db()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cls.owner_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, status, created_at, updated_at)
            VALUES (?, ?, 'Owner T10', 'clinician', 'local', 'active', ?, ?)
            """,
            (cls.owner_id, f"owner_t10_{uuid.uuid4().hex[:6]}@demo.test", now, now)
        )
        cls.clinic_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO clinics (id, slug, name, address_text, listing_type, verification_status, created_at, updated_at)
            VALUES (?, ?, 'Clinic T10', '999 Hai Ba Trung', 'partner_candidate', 'verified', ?, ?)
            """,
            (cls.clinic_id, f"clinic-t10-{uuid.uuid4().hex[:6]}", now, now)
        )
        cls.db.execute(
            """
            INSERT INTO clinician_profiles (user_id, clinic_id, clinic_role, verification_status, created_at, updated_at)
            VALUES (?, ?, 'owner', 'verified', ?, ?)
            """,
            (cls.owner_id, cls.clinic_id, now, now)
        )
        cls.db.commit()

    def test_01_T10_failed_tx_does_not_report_success(self):
        """T10: Failed settlement tx returns status='failed', not success."""
        res = purchase_partner_package(self.clinic_id, self.owner_id, simulate_tx_status="FAILED")
        self.assertEqual(res["status"], "failed")
        self.assertNotEqual(res["status"], "active")
        self.assertIsNone(res["partner_until"])

        # Check in DB
        clinic = self.db.execute("SELECT partner_until FROM clinics WHERE id = ?", (self.clinic_id,)).fetchone()
        self.assertIsNone(clinic["partner_until"])

if __name__ == "__main__":
    unittest.main()
