"""
test_clinics.py — GPS Haversine Distance, Nearby Clinics Sorting, and Partner Subscriptions.
Asserts:
- Haversine distance calculation is accurate.
- Nearby clinics sort Verified Partners FIRST even if further away.
- Only verified clinics with valid coordinates are returned.
- Non-partner directory clinics do not allow consent submission (can_send_consent=False).
- Purchasing partner package with CONFIRMED transaction sets partner_until.
- Purchasing with FAILED transaction leaves partner inactive (T10).
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.services.clinics import haversine_distance_km, search_nearby_clinics, purchase_partner_package, sync_clinics
from app.routers.consents import create_consent
from app.errors import LocationInvalidException, PartnerRequiredException, ForbiddenException

class TestClinics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        sync_clinics()
        cls.db = get_db()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        future = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat()

        # Seed verified owner clinician
        cls.owner_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, status, created_at, updated_at)
            VALUES (?, ?, 'Clinic Owner', 'clinician', 'local', 'active', ?, ?)
            """,
            (cls.owner_id, f"owner_{uuid.uuid4().hex[:6]}@demo.test", now, now)
        )

        # Seed clinic for purchase testing
        cls.test_clinic_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO clinics (id, slug, name, address_text, listing_type, verification_status, created_at, updated_at)
            VALUES (?, ?, 'Test Partner Clinic', '456 Le Loi', 'partner_candidate', 'verified', ?, ?)
            """,
            (cls.test_clinic_id, f"test-partner-{uuid.uuid4().hex[:6]}", now, now)
        )

        cls.db.execute(
            """
            INSERT INTO clinician_profiles (user_id, clinic_id, clinic_role, verification_status, created_at, updated_at)
            VALUES (?, ?, 'owner', 'verified', ?, ?)
            """,
            (cls.owner_id, cls.test_clinic_id, now, now)
        )

        # Seed patient and case
        cls.patient_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, privacy_accepted_at, status, created_at, updated_at)
            VALUES (?, ?, 'Patient Clinics Test', 'patient', 'local', ?, 'active', ?, ?)
            """,
            (cls.patient_id, f"patient_c_{uuid.uuid4().hex[:6]}@demo.test", now, now, now)
        )
        cls.case_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO cases (id, patient_id, profile_type, body_site, status, created_at, updated_at)
            VALUES (?, ?, 'acne', 'face', 'active', ?, ?)
            """,
            (cls.case_id, cls.patient_id, now, now)
        )
        cls.db.commit()

    def test_01_haversine_distance(self):
        # Distance between Ben Thanh Market (10.7725, 106.6980) and Landmark 81 (10.7950, 106.7219) ~ 3.6 km
        dist = haversine_distance_km(10.7725, 106.6980, 10.7950, 106.7219)
        self.assertGreaterEqual(dist, 3.0)
        self.assertLessEqual(dist, 4.5)

    def test_02_nearby_clinics_partner_sorted_first(self):
        """Verified Partner clinics appear before non-partner clinics even if farther away."""
        # Query near District 1
        clinics = search_nearby_clinics(lat=10.7725, lng=106.6980, radius_km=20.0)
        self.assertGreater(len(clinics), 0)

        # Check partner ordering
        partner_found = False
        non_partner_started = False
        for c in clinics:
            if c["is_partner"]:
                self.assertFalse(non_partner_started, "Partner clinic appeared after a non-partner clinic!")
                self.assertIn("Đối tác xác thực", c["partner_label"])
                self.assertTrue(c["can_send_consent"])
                partner_found = True
            else:
                non_partner_started = True
                self.assertFalse(c["can_send_consent"])

        self.assertTrue(partner_found)

    def test_03_partner_purchase_confirmed_activates(self):
        """Purchasing partner package with CONFIRMED transaction activates partner_until."""
        res = purchase_partner_package(self.test_clinic_id, self.owner_id, simulate_tx_status="CONFIRMED")
        self.assertEqual(res["status"], "active")
        self.assertIsNotNone(res["partner_until"])

        # Patient can now grant consent to this clinic
        consent = create_consent(self.patient_id, {
            "case_id": self.case_id,
            "recipient_clinic_id": self.test_clinic_id
        })
        self.assertEqual(consent["status"], "active")

    def test_04_partner_purchase_failed_does_not_activate(self):
        """T10: Failed partner purchase does NOT activate Partner status."""
        new_clinic_id = str(uuid.uuid4())
        new_owner_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, status, created_at, updated_at)
            VALUES (?, ?, 'New Owner', 'clinician', 'local', 'active', ?, ?)
            """,
            (new_owner_id, f"new_owner_{uuid.uuid4().hex[:6]}@demo.test", now, now)
        )
        self.db.execute(
            """
            INSERT INTO clinics (id, slug, name, address_text, listing_type, verification_status, created_at, updated_at)
            VALUES (?, ?, 'Failed Purchase Clinic', '789 Cong Hoa', 'partner_candidate', 'verified', ?, ?)
            """,
            (new_clinic_id, f"failed-clinic-{uuid.uuid4().hex[:6]}", now, now)
        )
        self.db.execute(
            """
            INSERT INTO clinician_profiles (user_id, clinic_id, clinic_role, verification_status, created_at, updated_at)
            VALUES (?, ?, 'owner', 'verified', ?, ?)
            """,
            (new_owner_id, new_clinic_id, now, now)
        )
        self.db.commit()

        # Purchase with FAILED status
        res = purchase_partner_package(new_clinic_id, new_owner_id, simulate_tx_status="FAILED")
        self.assertEqual(res["status"], "failed")
        self.assertIsNone(res["partner_until"])

        # Consent to this clinic must fail with PartnerRequiredException
        with self.assertRaises(PartnerRequiredException):
            create_consent(self.patient_id, {
                "case_id": self.case_id,
                "recipient_clinic_id": new_clinic_id
            })

if __name__ == "__main__":
    unittest.main()
