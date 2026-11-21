"""
test_cases.py — Unit tests for Cases, Observations, Symptoms, and YAML Profiles.
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.routers.cases import create_case, get_case, list_user_cases, close_case, create_observation, add_symptoms, get_case_symptoms, get_profile, list_profiles
from app.errors import ValidationException, ForbiddenException, NotFoundException

class TestCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = get_db()
        cls.patient_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, status, created_at, updated_at)
            VALUES (?, ?, 'Patient Test Cases', 'patient', 'local', 'active', ?, ?)
            """,
            (cls.patient_id, f"patient_cases_{uuid.uuid4().hex[:8]}@demo.test", now, now)
        )
        cls.db.commit()

    def test_01_load_all_profiles(self):
        profiles = list_profiles()
        self.assertGreaterEqual(len(profiles), 4)
        for p in profiles:
            self.assertIn("id", p)
            self.assertIn("disclaimer_vi", p)

        # Test specific profile load
        acne_prof = get_profile("acne")
        self.assertEqual(acne_prof["id"], "acne")
        self.assertEqual(acne_prof["cadence_days_default"], 7)

    def test_02_create_and_get_case(self):
        case = create_case(self.patient_id, {
            "profile_type": "acne",
            "body_site": "face",
            "title": "Mụn vùng má trái"
        })
        self.assertIn("id", case)
        self.assertEqual(case["diagnosis_status"], "unknown")
        self.assertEqual(case["status"], "active")

        # Get case
        retrieved = get_case(self.patient_id, case["id"])
        self.assertEqual(retrieved["id"], case["id"])

        # Other user cannot access
        stranger_id = str(uuid.uuid4())
        with self.assertRaises(ForbiddenException):
            get_case(stranger_id, case["id"])

    def test_03_observations_lifecycle(self):
        case = create_case(self.patient_id, {"profile_type": "eczema", "body_site": "arms"})
        obs = create_observation(self.patient_id, case["id"], {"notes": "Đợt ngứa đầu tuần"})
        self.assertEqual(obs["workflow_state"], "DRAFT")

    def test_04_symptoms_provenance(self):
        case = create_case(self.patient_id, {"profile_type": "other", "body_site": "back"})
        symptom = add_symptoms(self.patient_id, case["id"], {
            "form_version": "v1.0",
            "answers": {"itch": "many", "redness": "some", "fever": False}
        })
        self.assertEqual(symptom["provenance"], "user_reported")
        self.assertIn("itch", symptom["answers"])

        # Retrieve symptoms
        history = get_case_symptoms(self.patient_id, case["id"])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["answers"]["itch"], "many")

    def test_05_close_case(self):
        case = create_case(self.patient_id, {"profile_type": "psoriasis", "body_site": "legs"})
        res = close_case(self.patient_id, case["id"])
        self.assertEqual(res["status"], "closed")

        updated = get_case(self.patient_id, case["id"])
        self.assertEqual(updated["status"], "closed")

if __name__ == "__main__":
    unittest.main()
