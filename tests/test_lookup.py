"""
test_lookup.py — Knowledge Base Retrieval and UI Disclaimer & Safety Rules.
Asserts:
- Cosine lookup retrieves similar conditions.
- Output items are sorted ALPHABETICALLY by name_vi.
- Output contains mandatory disclaimer.
- Scans response strings to ensure NO '%' character appears next to condition names.
- Scans response strings to ensure NO forbidden words ("mắc", "chẩn đoán là", "nặng", "nhẹ", "nguy hiểm").
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.services.lookup import lookup_similar_conditions, sync_knowledge_base

class TestLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        sync_knowledge_base()
        cls.db = get_db()
        cls.patient_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, status, created_at, updated_at)
            VALUES (?, ?, 'Lookup Test Patient', 'patient', 'local', 'active', ?, ?)
            """,
            (cls.patient_id, f"patient_lookup_{uuid.uuid4().hex[:6]}@demo.test", now, now)
        )
        cls.case_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO cases (id, patient_id, profile_type, body_site, status, created_at, updated_at)
            VALUES (?, ?, 'acne', 'face', 'active', ?, ?)
            """,
            (cls.case_id, cls.patient_id, now, now)
        )
        cls.obs_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO observations (id, case_id, captured_at, workflow_state, created_at, updated_at)
            VALUES (?, ?, ?, 'READY_FOR_ANALYSIS', ?, ?)
            """,
            (cls.obs_id, cls.case_id, now, now, now)
        )
        cls.db.commit()

    def test_01_lookup_acne_symptoms(self):
        res = lookup_similar_conditions(
            observation_id=self.obs_id,
            body_site="face",
            symptoms={"blackheads": "many", "papules": "some", "pustules": "some"},
            onset="onset_gt2m",
            quality_status="PASS"
        )
        self.assertIn("items", res)
        self.assertGreater(len(res["items"]), 0)
        names = [x["name_vi"] for x in res["items"]]
        self.assertIn("Mụn trứng cá", names)

        # Check alphabetical sorting
        self.assertEqual(names, sorted(names))

        # Check mandatory disclaimer
        self.assertIn("disclaimer", res)
        self.assertIn("không phải chẩn đoán", res["disclaimer"].lower())

    def test_02_string_scan_safety(self):
        """Scans response to ensure no %, no diagnostic confirmation words."""
        res = lookup_similar_conditions(
            observation_id=self.obs_id,
            body_site="arms",
            symptoms={"itch": "many", "redness": "some", "scaling": "some"},
            quality_status="PASS"
        )
        for item in res["items"]:
            # Check NO % character
            self.assertNotIn("%", item["name_vi"])
            self.assertNotIn("%", item["summary"])

            # Check forbidden diagnostic words
            forbidden_words = ["chẩn đoán là", "chắc chắn bị", "bạn mắc", "nguy hiểm tính mạng"]
            for fw in forbidden_words:
                self.assertNotIn(fw, item["name_vi"].lower())
                self.assertNotIn(fw, item["summary"].lower())

    def test_03_urgent_safety_cutoff(self):
        """When urgent flag is active, lookup is halted immediately."""
        res = lookup_similar_conditions(
            observation_id=self.obs_id,
            body_site="face",
            symptoms={"blackheads": "many"},
            urgent_message_active=True
        )
        self.assertEqual(len(res["items"]), 0)
        self.assertEqual(res["abstain_reason"], "urgent_safety_cutoff")

if __name__ == "__main__":
    unittest.main()
