"""
test_quality.py — T01: Image Quality Assessment & Quality Gate.
Asserts:
- Blur or dark image -> RETAKE.
- Sharp image with good exposure -> PASS.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("apps/api"))

from ml.vision.quality import assess_image_quality
from ml.fixtures.synthetic_images import generate_sharp_skin_image, generate_blurry_image, generate_dark_image

class TestQualityGate(unittest.TestCase):
    def test_01_T01_sharp_image_passes(self):
        """Sharp synthetic image should pass quality gate."""
        sharp_bytes = generate_sharp_skin_image()
        report = assess_image_quality(sharp_bytes)
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["metrics"]["sharpness_score"], 60.0)

    def test_02_T01_blur_triggers_retake(self):
        """T01: Heavily blurred image triggers RETAKE status."""
        blur_bytes = generate_blurry_image()
        report = assess_image_quality(blur_bytes)
        self.assertEqual(report["status"], "RETAKE")
        self.assertTrue(any("mờ" in r.lower() for r in report["reasons"]))

    def test_03_T01_dark_triggers_retake(self):
        """T01: Underexposed / dark image triggers RETAKE status."""
        dark_bytes = generate_dark_image()
        report = assess_image_quality(dark_bytes)
        self.assertEqual(report["status"], "RETAKE")
        self.assertTrue(any("tối" in r.lower() or "sáng" in r.lower() for r in report["reasons"]))

    def test_04_T01_moderate_resolution_image_passes(self):
        """Moderate resolution (e.g. 303px, 480px) and sharpness >= 15 passes gate."""
        from PIL import Image, ImageDraw
        import io
        img = Image.new("RGB", (320, 303), color=(220, 180, 150))
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 100, 200, 200], fill=(200, 80, 70))
        for i in range(50, 250, 10):
            draw.line([i, 80, i, 220], fill=(230, 190, 160), width=1)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        report = assess_image_quality(buf.getvalue())
        self.assertIn(report["status"], ["PASS", "REVIEW"])

if __name__ == "__main__":
    unittest.main()
