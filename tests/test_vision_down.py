"""
test_vision_down.py — T09: Vision Service Failure & Error Isolation.
Asserts:
- When vision service is down or encounters an exception, it raises MODEL_UNAVAILABLE.
- It NEVER returns stale numbers or cached previous measurements as new!
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("apps/api"))

from ml.vision.measure import measure_observation
from ml.fixtures.synthetic_images import generate_sharp_skin_image
from app.errors import ModelUnavailableException

class TestVisionDown(unittest.TestCase):
    def test_01_T09_vision_failure_raises_model_unavailable(self):
        """T09: Simulated vision failure raises MODEL_UNAVAILABLE instead of returning stale data."""
        img_bytes = generate_sharp_skin_image()
        with self.assertRaises(ModelUnavailableException):
            measure_observation(img_bytes, body_site="face", simulate_failure=True)

    def test_02_T09_corrupted_image_raises_model_unavailable(self):
        corrupted_bytes = b"NOT_A_VALID_IMAGE_DATA_BYTES"
        with self.assertRaises(ModelUnavailableException):
            measure_observation(corrupted_bytes, body_site="face")

if __name__ == "__main__":
    unittest.main()
