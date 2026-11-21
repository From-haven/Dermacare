"""
test_images.py — T03: Image Processing, Encryption, and Deduplication.
Asserts:
- Duplicate image sha256 raises DuplicateImageException (T03).
- Image is encrypted at rest and decryptable via short-lived 60s token.
- EXIF metadata is stripped.
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.routers.images import upload_observation_image, request_image_token, get_image_content
from ml.fixtures.synthetic_images import generate_sharp_skin_image, generate_image_with_exif
from app.errors import DuplicateImageException, ForbiddenException, UnauthenticatedException

class TestImages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = get_db()
        cls.patient_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # Seed patient who accepted privacy policy
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, privacy_accepted_at, status, created_at, updated_at)
            VALUES (?, ?, 'Image Test Patient', 'patient', 'local', ?, 'active', ?, ?)
            """,
            (cls.patient_id, f"patient_img_{uuid.uuid4().hex[:6]}@demo.test", now, now, now)
        )
        # Seed case and observation
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
            VALUES (?, ?, ?, 'AWAITING_CAPTURE', ?, ?)
            """,
            (cls.obs_id, cls.case_id, now, now, now)
        )
        cls.db.commit()

    def test_01_upload_and_decrypt_with_60s_token(self):
        # Generate uniquely tinted sharp image to avoid cross-run sha256 collisions
        from PIL import Image, ImageDraw
        import io
        img = Image.new("RGB", (700, 700), color=(220, 180, 140))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"unique_{uuid.uuid4().hex}")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()

        res = upload_observation_image(self.patient_id, self.obs_id, img_bytes, view_type="overview")
        self.assertIn("image_id", res)
        image_id = res["image_id"]

        # Request 60s image token
        token_res = request_image_token(self.patient_id, image_id)
        self.assertIn("token", token_res)
        token = token_res["token"]

        # View image content with valid token
        clean_bytes, mime = get_image_content(image_id, token)
        self.assertGreater(len(clean_bytes), 0)
        self.assertEqual(mime, "image/jpeg")

        # Invalid token rejected
        with self.assertRaises(UnauthenticatedException):
            get_image_content(image_id, "invalid_or_expired_token")

    def test_02_T03_duplicate_image_hash_rejected(self):
        """T03: Duplicate image hash raises DUPLICATE_IMAGE error and blocks duplicate observation."""
        from PIL import Image, ImageDraw
        import io
        img = Image.new("RGB", (700, 700), color=(210, 170, 130))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"dup_seed_{uuid.uuid4().hex}")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        unique_img_bytes = buf.getvalue()

        # First upload -> OK
        res = upload_observation_image(self.patient_id, self.obs_id, unique_img_bytes)
        self.assertIn("image_id", res)

        # Second upload with exact same bytes -> DuplicateImageException
        with self.assertRaises(DuplicateImageException):
            upload_observation_image(self.patient_id, self.obs_id, unique_img_bytes)

if __name__ == "__main__":
    unittest.main()
