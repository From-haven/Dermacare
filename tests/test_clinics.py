"""
test_clinics.py — GPS Haversine Distance, Dual Independent Clinic Lists, and Partner Subscriptions.
Asserts:
- Haversine distance calculation is accurate.
- Nearby search returns 2 independent, disjoint lists: `nearby_clinics` and `partner_clinics`.
- `nearby_clinics` contains only non-partner hospitals/clinics sorted strictly by nearest GPS distance ASC.
- `partner_clinics` contains only verified partner clinics sorted strictly by nearest GPS distance ASC.
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

    def test_02_nearby_clinics_two_independent_lists_sorted_by_distance(self):
        """Nearby search returns 2 independent, disjoint lists each sorted strictly by nearest distance ASC."""
        # Query near District 1
        res = search_nearby_clinics(lat=10.7725, lng=106.6980, radius_km=20.0)
        self.assertIsInstance(res, dict)
        self.assertIn("nearby_clinics", res)
        self.assertIn("partner_clinics", res)

        nearby = res["nearby_clinics"]
        partners = res["partner_clinics"]
        self.assertGreater(len(nearby), 0)
        self.assertGreater(len(partners), 0)

        # Verify nearby_clinics are all non-partner and strictly sorted by distance ASC
        nearby_distances = []
        for c in nearby:
            self.assertFalse(c["is_partner"], "Partner clinic should not appear in nearby_clinics list!")
            self.assertFalse(c["can_send_consent"])
            nearby_distances.append(c["distance_km"])
        self.assertEqual(nearby_distances, sorted(nearby_distances), "nearby_clinics must be sorted nearest first!")

        # Verify partner_clinics are all verified partners and strictly sorted by distance ASC
        partner_distances = []
        for c in partners:
            self.assertTrue(c["is_partner"], "Non-partner clinic should not appear in partner_clinics list!")
            self.assertIn("Đối tác xác thực", c["partner_label"])
            self.assertTrue(c["can_send_consent"])
            partner_distances.append(c["distance_km"])
        self.assertEqual(partner_distances, sorted(partner_distances), "partner_clinics must be sorted nearest first!")

        # Verify the 2 lists are completely disjoint
        nearby_ids = {c["id"] for c in nearby}
        partner_ids = {c["id"] for c in partners}
        self.assertEqual(nearby_ids.intersection(partner_ids), set())

    def test_02b_nearest_hospital_matches_gps_location(self):
        """The #1 clinic in nearby_clinics must be the geographically closest hospital to the user's GPS."""
        # Near BV FV (Quận 7: 10.7303, 106.7218)
        res_q7 = search_nearby_clinics(lat=10.7305, lng=106.7220, radius_km=20.0)
        self.assertIn("FV", res_q7["nearby_clinics"][0]["name"])
        self.assertLess(res_q7["nearby_clinics"][0]["distance_km"], 0.5)

        # Near BV Da liễu TP.HCM (Quận 3: 10.7782, 106.6853)
        res_q3 = search_nearby_clinics(lat=10.7783, lng=106.6854, radius_km=20.0)
        self.assertIn("Bệnh viện Da liễu TP.HCM", res_q3["nearby_clinics"][0]["name"])
        self.assertLess(res_q3["nearby_clinics"][0]["distance_km"], 0.5)

        # Near BV Đại học Y Dược TP.HCM (Quận 5: 10.7554, 106.6586)
        res_q5 = search_nearby_clinics(lat=10.7554, lng=106.6586, radius_km=20.0)
        self.assertIn("Đại học Y Dược", res_q5["nearby_clinics"][0]["name"])
        self.assertLess(res_q5["nearby_clinics"][0]["distance_km"], 0.5)

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
