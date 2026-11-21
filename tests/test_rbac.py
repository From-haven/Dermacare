"""
test_rbac.py — Unit tests for RBAC matrix and immediate Consent enforcement.
Maps to T05 & T06 requirements in Section 7 & 18.
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.core.rbac import check_patient_owns_case, check_clinician_has_consent, enforce_admin
from app.errors import ForbiddenException, ConsentRequiredException, ConsentExpiredException, PartnerRequiredException

class TestRBAC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = get_db()
        cls.now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cls.future = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat()
        cls.past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()

        # Seed test clinic (verified + active partner) with unique slug
        cls.clinic_id = str(uuid.uuid4())
        unique_slug = f"test-clinic-rbac-{uuid.uuid4().hex[:6]}"
        cls.db.execute(
            """
            INSERT INTO clinics (id, slug, name, address_text, listing_type, verification_status, partner_until, created_at, updated_at)
            VALUES (?, ?, 'Test Clinic RBAC', '123 Test St', 'partner', 'verified', ?, ?, ?)
            """,
            (cls.clinic_id, unique_slug, cls.future, cls.now, cls.now)
        )

        # Seed verified clinician
        cls.doc_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO users (id, email, role, auth_provider, created_at, updated_at)
            VALUES (?, ?, 'clinician', 'local', ?, ?)
            """,
            (cls.doc_id, f"doc_rbac_{uuid.uuid4().hex[:6]}@demo.test", cls.now, cls.now)
        )
        cls.db.execute(
            """
            INSERT INTO clinician_profiles (user_id, clinic_id, clinic_role, verification_status, created_at, updated_at)
            VALUES (?, ?, 'doctor', 'verified', ?, ?)
            """,
            (cls.doc_id, cls.clinic_id, cls.now, cls.now)
        )

        # Seed patient and case
        cls.patient_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO users (id, email, role, auth_provider, created_at, updated_at)
            VALUES (?, ?, 'patient', 'local', ?, ?)
            """,
            (cls.patient_id, f"patient_rbac_{uuid.uuid4().hex[:6]}@demo.test", cls.now, cls.now)
        )
        cls.case_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO cases (id, patient_id, profile_type, body_site, status, created_at, updated_at)
            VALUES (?, ?, 'acne', 'face', 'active', ?, ?)
            """,
            (cls.case_id, cls.patient_id, cls.now, cls.now)
        )
        cls.db.commit()

    def test_01_patient_owns_case(self):
        # Patient owns case -> OK
        c = check_patient_owns_case(self.patient_id, self.case_id)
        self.assertEqual(c["id"], self.case_id)

        # Other user -> ForbiddenException
        stranger_id = str(uuid.uuid4())
        with self.assertRaises(ForbiddenException):
            check_patient_owns_case(stranger_id, self.case_id)

    def test_02_T05_clinician_no_consent_403(self):
        """T05: Clinician without consent receives 403 (CONSENT_REQUIRED) + audit deny."""
        with self.assertRaises(ConsentRequiredException):
            check_clinician_has_consent(self.doc_id, self.case_id)

    def test_03_clinician_with_active_consent_ok(self):
        # Grant consent
        consent_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO consents (id, patient_id, case_id, recipient_clinic_id, scope, expires_at, status, commitment, nonce_enc, created_at, updated_at)
            VALUES (?, ?, ?, ?, '{"images": true, "measurements": true}', ?, 'active', '0x123', 'enc_nonce', ?, ?)
            """,
            (consent_id, self.patient_id, self.case_id, self.clinic_id, self.future, self.now, self.now)
        )
        self.db.commit()

        # Check access -> OK
        res = check_clinician_has_consent(self.doc_id, self.case_id, required_scope_item="images")
        self.assertEqual(res["id"], consent_id)

    def test_04_T06_consent_revocation_immediate_403(self):
        """T06: When consent is revoked, next clinician request immediately returns 403."""
        # Revoke consent
        self.db.execute(
            "UPDATE consents SET status = 'revoked', revoked_at = ? WHERE case_id = ? AND recipient_clinic_id = ?",
            (self.now, self.case_id, self.clinic_id)
        )
        self.db.commit()

        with self.assertRaises(ConsentExpiredException):
            check_clinician_has_consent(self.doc_id, self.case_id)

    def test_05_admin_enforcement(self):
        # Admin check passes for admin
        enforce_admin("admin", "admin-id", "verify_clinic")

        # Patient attempting admin action -> 403
        with self.assertRaises(ForbiddenException):
            enforce_admin("patient", self.patient_id, "verify_clinic")

if __name__ == "__main__":
    unittest.main()
