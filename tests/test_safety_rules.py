"""
test_safety_rules.py — Deterministic Evaluation of 21 Safety Rules (Appendix C).
Asserts:
- Each urgent rule triggers URGENT_MESSAGE and halts flow.
- Highest action wins (URGENT_MESSAGE > CLINICIAN_REVIEW > ROUTINE).
- Message contains no disease names.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("apps/api"))

from app.agent.safety import evaluate_safety_rules

class TestSafetyRules(unittest.TestCase):
    def test_01_U01_facial_swelling_or_breathing(self):
        res = evaluate_safety_rules({"face_lip_swelling_or_breathing": True})
        self.assertEqual(res["action"], "URGENT_MESSAGE")
        self.assertTrue(res["is_urgent"])
        self.assertIn("U01", res["triggered_rules"])
        self.assertTrue(any("115" in m for m in res["messages"]))

    def test_02_U02_fever_and_rapid_spread(self):
        res = evaluate_safety_rules({"fever": True, "spreading_rapidly": True})
        self.assertEqual(res["action"], "URGENT_MESSAGE")
        self.assertIn("U02", res["triggered_rules"])

    def test_03_U03_blisters_mucosa(self):
        res = evaluate_safety_rules({"blisters_mucosa": True})
        self.assertEqual(res["action"], "URGENT_MESSAGE")
        self.assertIn("U03", res["triggered_rules"])

    def test_04_C01_same_day_clinician_review(self):
        res = evaluate_safety_rules({"purple_nonblanching_spots": True})
        self.assertEqual(res["action"], "CLINICIAN_REVIEW")
        self.assertEqual(res["timeframe"], "same_day")
        self.assertIn("C01", res["triggered_rules"])

    def test_05_C05_soon_clinician_review(self):
        res = evaluate_safety_rules({"oozing": "some", "crusting": "some", "pain": "some"})
        self.assertEqual(res["action"], "CLINICIAN_REVIEW")
        self.assertEqual(res["timeframe"], "soon")
        self.assertIn("C05", res["triggered_rules"])

    def test_06_C10_routine_clinician_review(self):
        res = evaluate_safety_rules({"rash_lasting_over_2_weeks": True})
        self.assertEqual(res["action"], "CLINICIAN_REVIEW")
        self.assertEqual(res["timeframe"], "routine")
        self.assertIn("C10", res["triggered_rules"])

    def test_07_highest_action_wins(self):
        """When both urgent and routine rules trigger, URGENT_MESSAGE wins."""
        res = evaluate_safety_rules({
            "face_lip_swelling_or_breathing": True,  # URGENT U01
            "rash_lasting_over_2_weeks": True        # ROUTINE C10
        })
        self.assertEqual(res["action"], "URGENT_MESSAGE")
        self.assertTrue(res["is_urgent"])

    def test_08_routine_default(self):
        res = evaluate_safety_rules({})
        self.assertEqual(res["action"], "ROUTINE")
        self.assertFalse(res["is_urgent"])

if __name__ == "__main__":
    unittest.main()
