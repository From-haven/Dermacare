"""
reports.py router — API endpoints for generating and retrieving reports.
"""
from app.core.rbac import check_patient_owns_case
from app.services.reports import generate_case_report
from app.core.audit import record_audit_event
from app.core.db import get_db
import uuid
import datetime
import json

def create_report(user_id: str, case_id: str, audience: str = "patient", ip: str = "127.0.0.1") -> dict:
    check_patient_owns_case(user_id, case_id, ip)
    report_data = generate_case_report(case_id, audience)

    report_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db = get_db()
    db.execute(
        """
        INSERT INTO reports (id, case_id, version, audience, content, generated_by, created_at, updated_at)
        VALUES (?, ?, 'v1.0', ?, ?, 'template', ?, ?)
        """,
        (report_id, case_id, audience, json.dumps(report_data), now, now)
    )
    db.commit()

    record_audit_event(user_id, "patient", "generate_report", "report", report_id, "allow", ip)
    return {"report_id": report_id, "case_id": case_id, "audience": audience, "generated_at": now}

def get_report(report_id: str, user_id: str, ip: str = "127.0.0.1") -> dict:
    db = get_db()
    row = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        raise ValueError("Report not found")
    report = dict(row)
    report["content"] = json.loads(report["content"]) if isinstance(report["content"], str) else report["content"]
    record_audit_event(user_id, "user", "view_report", "report", report_id, "allow", ip)
    return report
