"""
test_compare.py — T02: Observation Comparability and Deltas.
Asserts:
- Observations on different body sites return NOT_COMPARABLE and empty deltas (T02).
- Observations with same site and good quality return COMPARABLE and compute deltas.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("apps/api"))

from ml.vision.compare import evaluate_comparability

class TestCompare(unittest.TestCase):
    def test_01_T02_different_site_is_not_comparable(self):
        """T02: Different body_site returns NOT_COMPARABLE and empty deltas."""
        obs_a = {
            "case_id": "case-123",
            "body_site": "face",
            "view_type": "overview",
            "quality_status": "PASS",
            "affected_area_ratio": 15.0
        }
        obs_b = {
            "case_id": "case-123",
            "body_site": "back",  # Different site!
            "view_type": "overview",
            "quality_status": "PASS",
            "affected_area_ratio": 12.0
        }
        res = evaluate_comparability(obs_a, obs_b)
        self.assertEqual(res["flag"], "NOT_COMPARABLE")
        self.assertEqual(res["deltas"], {})
        self.assertTrue(any("vùng chụp khác nhau" in r.lower() for r in res["reasons"]))

    def test_02_different_case_is_not_comparable(self):
        obs_a = {"case_id": "case-1", "body_site": "face", "quality_status": "PASS"}
        obs_b = {"case_id": "case-2", "body_site": "face", "quality_status": "PASS"}
        res = evaluate_comparability(obs_a, obs_b)
        self.assertEqual(res["flag"], "NOT_COMPARABLE")
        self.assertEqual(res["deltas"], {})

    def test_03_same_site_comparable_computes_deltas(self):
        obs_a = {
            "case_id": "case-123",
            "body_site": "arms",
            "view_type": "overview",
            "quality_status": "PASS",
            "l_median": 52.0,
            "roi_area": 100.0,
            "affected_area_ratio": 18.5
        }
        obs_b = {
            "case_id": "case-123",
            "body_site": "arms",
            "view_type": "overview",
            "quality_status": "PASS",
            "l_median": 54.0,
            "roi_area": 105.0,
            "affected_area_ratio": 14.2
        }
        res = evaluate_comparability(obs_a, obs_b)
        self.assertEqual(res["flag"], "COMPARABLE")
        self.assertIn("delta_affected_area_ratio", res["deltas"])
        self.assertAlmostEqual(res["deltas"]["delta_affected_area_ratio"], -4.3, places=1)

if __name__ == "__main__":
    unittest.main()
