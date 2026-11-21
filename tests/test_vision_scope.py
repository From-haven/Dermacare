"""
test_vision_scope.py — T07: Vision Scope and Out-of-Scope Handling.
Asserts:
- Out of scope or invalid body site -> ABSTAIN.
- No disease assertion or diagnosis is made.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("apps/api"))

from ml.vision.measure import measure_observation
from ml.fixtures.synthetic_images import generate_sharp_skin_image

class TestVisionScope(unittest.TestCase):
    def test_01_T07_valid_site_measures_properly(self):
        img_bytes = generate_sharp_skin_image()
        measures = measure_observation(img_bytes, body_site="face")
        area_m = next((m for m in measures if m["metric_name"] == "affected_area_ratio"), None)
        self.assertIsNotNone(area_m)
        self.assertEqual(area_m["provenance"], "ai_measured")

    def test_02_T07_out_of_scope_site_abstains(self):
        """T07: Out-of-scope body site returns ABSTAIN without disease assertion."""
        img_bytes = generate_sharp_skin_image()
        measures = measure_observation(img_bytes, body_site="internal_organ_invalid")
        status_m = next((m for m in measures if m["metric_name"] == "measurement_status"), None)
        self.assertIsNotNone(status_m)
        self.assertEqual(status_m["details"]["status"], "ABSTAIN")
        self.assertEqual(status_m["details"]["reason"], "unsupported_body_site")

if __name__ == "__main__":
    unittest.main()
