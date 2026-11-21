"""
clinician.py router — Doctor Dashboard and Clinical Reviews.
Endpoints:
- GET /api/clinician/patients: list patients who shared consent to doctor's clinic.
- GET /api/clinician/cases/{id}: view case record under active consent.
- POST /api/clinician/cases/{id}/review: record clinician review and score.
"""
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.core.rbac import check_clinician_has_consent
from app.errors import ForbiddenException, NotFoundException
import uuid
import datetime
import json

def get_clinician_inbox(clinician_id: str, ip: str = "127.0.0.1") -> list:
    db = get_db()
    # Check clinician profile & clinic
    prof = db.execute(
        """
        SELECT cp.*, c.partner_until, c.verification_status as clinic_verif
        FROM clinician_profiles cp
        JOIN clinics c ON cp.clinic_id = c.id
        WHERE cp.user_id = ?
        """,
        (clinician_id,)
    ).fetchone()

    if not prof or prof["verification_status"] != "verified" or prof["clinic_verif"] != "verified":
        raise ForbiddenException("Bác sĩ hoặc phòng khám chưa được xác thực")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not prof["partner_until"] or prof["partner_until"] < now_iso:
        raise ForbiddenException("Phòng khám chưa mua hoặc đã hết hạn gói Verified Partner")

    clinic_id = prof["clinic_id"]

    rows = db.execute(
        """
        SELECT c.id as consent_id, c.case_id, c.patient_id, c.scope, c.expires_at,
               cs.body_site, cs.profile_type, cs.title as case_title,
               u.display_name as patient_name
        FROM consents c
        JOIN cases cs ON c.case_id = cs.id
        JOIN users u ON c.patient_id = u.id
        WHERE c.recipient_clinic_id = ? AND c.status = 'active' AND c.expires_at > ?
        ORDER BY c.created_at DESC
        """,
        (clinic_id, now_iso)
    ).fetchall()

    record_audit_event(clinician_id, "clinician", "view_inbox", "clinician_inbox", clinic_id, "allow", ip)
    return [dict(r) for r in rows]

def get_case_for_clinician(clinician_id: str, case_id: str, ip: str = "127.0.0.1") -> dict:
    consent = check_clinician_has_consent(clinician_id, case_id, ip=ip)
    db = get_db()
    case = db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    observations = db.execute("SELECT * FROM observations WHERE case_id = ? ORDER BY captured_at DESC", (case_id,)).fetchall()
    symptoms = db.execute("SELECT * FROM symptom_entries WHERE case_id = ? ORDER BY entered_at DESC", (case_id,)).fetchall()

    record_audit_event(clinician_id, "clinician", "view_case_full", "case", case_id, "allow", ip)
    return {
        "case": dict(case),
        "consent": consent,
        "observations": [dict(o) for o in observations],
        "symptoms": [dict(s) for s in symptoms]
    }

def record_clinician_review(clinician_id: str, case_id: str, data: dict, ip: str = "127.0.0.1") -> dict:
    check_clinician_has_consent(clinician_id, case_id, ip=ip)
    note = data.get("note", "")
    clinician_scores = data.get("clinician_scores", [])  # [{name, value, scale}]
    plan = data.get("plan", {})
    next_followup_at = data.get("next_followup_at")

    rev_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db = get_db()
    db.execute(
        """
        INSERT INTO clinician_reviews (
            id, case_id, clinician_id, note, clinician_scores, plan, next_followup_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (rev_id, case_id, clinician_id, note, json.dumps(clinician_scores), json.dumps(plan), next_followup_at, now, now)
    )
    db.commit()

    record_audit_event(clinician_id, "clinician", "record_review", "clinician_review", rev_id, "allow", ip)
    return {
        "id": rev_id,
        "case_id": case_id,
        "clinician_id": clinician_id,
        "provenance": "clinician_entered",
        "created_at": now
    }
