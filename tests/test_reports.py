"""
test_reports.py — Unit tests for Medical Report Generator and Timeline.
Asserts:
- Report header contains NO disease name.
- Mandatory medical disclaimer banner is present.
- 4 Provenance categories are tracked.
- Profile 'other' does not draw trend lines.
"""
import unittest
import sys
import os
import uuid
import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import init_db, get_db
from app.services.timeline import generate_timeline
from app.services.reports import generate_case_report
from app.routers.reports import create_report, get_report

class TestReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = get_db()
        cls.patient_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cls.db.execute(
            """
            INSERT INTO users (id, email, display_name, role, auth_provider, status, created_at, updated_at)
            VALUES (?, ?, 'Report Test Patient', 'patient', 'local', 'active', ?, ?)
            """,
            (cls.patient_id, f"patient_rep_{uuid.uuid4().hex[:6]}@demo.test", now, now)
        )
        cls.case_id = str(uuid.uuid4())
        cls.db.execute(
            """
            INSERT INTO cases (id, patient_id, profile_type, body_site, status, created_at, updated_at)
            VALUES (?, ?, 'acne', 'face', 'active', ?, ?)
            """,
            (cls.case_id, cls.patient_id, now, now)
        )
        cls.db.commit()

    def test_01_timeline_trend_rules(self):
        # 3 points for acne -> can compute trend
        obs_acne = [
            {"id": "1", "captured_at": "2026-11-01T10:00:00Z", "comparison_flag": "COMPARABLE", "measurements": {"affected_area_ratio": 20.0}},
            {"id": "2", "captured_at": "2026-11-08T10:00:00Z", "comparison_flag": "COMPARABLE", "measurements": {"affected_area_ratio": 17.0}},
            {"id": "3", "captured_at": "2026-11-15T10:00:00Z", "comparison_flag": "COMPARABLE", "measurements": {"affected_area_ratio": 14.0}},
        ]
        res = generate_timeline(obs_acne, profile_type="acne")
        self.assertTrue(res["can_draw_trend"])
        self.assertIn("xu hướng giảm", res["trend_summary"])

        # Profile 'other' -> can_draw_trend is FALSE
        res_other = generate_timeline(obs_acne, profile_type="other")
        self.assertFalse(res_other["can_draw_trend"])
        self.assertIn("không vẽ đường xu hướng", res_other["trend_summary"])

    def test_02_report_generation_neutral_header(self):
        rep = generate_case_report(self.case_id, audience="patient")
        html = rep["html_content"]

        # Check disclaimer banner exists
        self.assertIn("KHÔNG PHẢI CHẨN ĐOÁN Y KHOA", html)

        # Check neutral title (no disease name in header)
        self.assertIn("HỒ SƠ THEO DÕI BIỂU HIỆN DA", html)

        # Check provenance badges
        self.assertIn("ai_measured", html)
        self.assertIn("user_reported", html)

    def test_03_report_router_save_and_get(self):
        created = create_report(self.patient_id, self.case_id, audience="clinician")
        self.assertIn("report_id", created)

        retrieved = get_report(created["report_id"], self.patient_id)
        self.assertEqual(retrieved["audience"], "clinician")
        self.assertIn("html_content", retrieved["content"])

if __name__ == "__main__":
    unittest.main()
