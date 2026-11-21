"""
test_state_machine.py — Unit tests for Observation Workflow State Machine.
Verifies valid transitions and rejection of invalid hops.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.state_machine import transition, can_transition
from app.errors import ValidationException

class TestStateMachine(unittest.TestCase):
    def test_01_valid_happy_path(self):
        # DRAFT -> AWAITING_CAPTURE
        s1 = transition("DRAFT", "AWAITING_CAPTURE")
        self.assertEqual(s1, "AWAITING_CAPTURE")

        # AWAITING_CAPTURE -> READY_FOR_ANALYSIS
        s2 = transition(s1, "READY_FOR_ANALYSIS")
        self.assertEqual(s2, "READY_FOR_ANALYSIS")

        # READY_FOR_ANALYSIS -> OBSERVATION_CREATED
        s3 = transition(s2, "OBSERVATION_CREATED")
        self.assertEqual(s3, "OBSERVATION_CREATED")

        # OBSERVATION_CREATED -> TIMELINE_UPDATED
        s4 = transition(s3, "TIMELINE_UPDATED")
        self.assertEqual(s4, "TIMELINE_UPDATED")

        # TIMELINE_UPDATED -> REPORT_READY
        s5 = transition(s4, "REPORT_READY")
        self.assertEqual(s5, "REPORT_READY")

    def test_02_retake_path(self):
        # AWAITING_CAPTURE -> QUALITY_REJECTED
        s1 = transition("AWAITING_CAPTURE", "QUALITY_REJECTED")
        self.assertEqual(s1, "QUALITY_REJECTED")

        # QUALITY_REJECTED -> AWAITING_CAPTURE (retake)
        s2 = transition(s1, "AWAITING_CAPTURE")
        self.assertEqual(s2, "AWAITING_CAPTURE")

    def test_03_invalid_transitions_rejected(self):
        # Cannot jump from DRAFT directly to REPORT_READY
        with self.assertRaises(ValidationException):
            transition("DRAFT", "REPORT_READY")

        # Cannot jump from QUALITY_REJECTED directly to OBSERVATION_CREATED
        with self.assertRaises(ValidationException):
            transition("QUALITY_REJECTED", "OBSERVATION_CREATED")

        # Terminal state cannot transition anywhere
        self.assertFalse(can_transition("REPORT_READY", "DRAFT"))
        with self.assertRaises(ValidationException):
            transition("REPORT_READY", "DRAFT")

if __name__ == "__main__":
    unittest.main()
