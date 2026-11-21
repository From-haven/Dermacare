"""
test_consent_upload.py — T04: Privacy Policy Acceptance Enforcement.
Asserts:
- User who has NOT accepted privacy policy is blocked from uploading images (T04).
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.routers.images import upload_observation_image
from ml.fixtures.synthetic_images import generate_sharp_skin_image
from app.errors import ForbiddenException

class TestConsentUpload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = get_db()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # User WITHOUT privacy acceptance
        cls.unconsented_user_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, privacy_accepted_at, status, created_at, updated_at)
            VALUES (?, ?, 'Unconsented Patient', 'patient', 'local', NULL, 'active', ?, ?)
            """,
            (cls.unconsented_user_id, f"unconsented_{uuid.uuid4().hex[:6]}@demo.test", now, now)
        )

        cls.case_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO cases (id, patient_id, profile_type, body_site, status, created_at, updated_at)
            VALUES (?, ?, 'acne', 'face', 'active', ?, ?)
            """,
            (cls.case_id, cls.unconsented_user_id, now, now)
        )

        cls.obs_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO observations (id, case_id, captured_at, workflow_state, created_at, updated_at)
            VALUES (?, ?, ?, 'AWAITING_CAPTURE', ?, ?)
            """,
            (cls.obs_id, cls.case_id, now, now, now)
        )
        cls.db.commit()

    def test_01_T04_unconsented_upload_blocked(self):
        """T04: Uploading before privacy acceptance must raise ForbiddenException."""
        img_bytes = generate_sharp_skin_image()
        with self.assertRaises(ForbiddenException):
            upload_observation_image(self.unconsented_user_id, self.obs_id, img_bytes)

if __name__ == "__main__":
    unittest.main()
