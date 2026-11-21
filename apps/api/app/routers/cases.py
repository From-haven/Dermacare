"""
cases.py — Router and service for Cases, Observations, Symptoms, and Profiles.
"""
import uuid
import os
import json
import yaml
import datetime
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.core.rbac import check_patient_owns_case
from app.services.state_machine import transition
from app.errors import ValidationException, NotFoundException, ForbiddenException

PROFILES_DIR = "apps/api/app/profiles"

def get_profile(profile_type: str) -> dict:
    """Load profile definition from YAML."""
    file_path = os.path.join(PROFILES_DIR, f"{profile_type}.yaml")
    if not os.path.exists(file_path):
        raise NotFoundException(f"Profile '{profile_type}' không tồn tại")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def list_profiles() -> list:
    """List all available profiles."""
    profiles = []
    for p in ["intake_general", "acne", "eczema", "psoriasis", "other"]:
        try:
            prof = get_profile(p)
            profiles.append({
                "id": prof["id"],
                "version": prof["version"],
                "label_vi": prof["label_vi"],
                "label_en": prof.get("label_en", ""),
                "body_sites": prof.get("body_sites", []),
                "disclaimer_vi": prof.get("disclaimer_vi", "")
            })
        except Exception:
            pass
    return profiles

def create_case(user_id: str, data: dict, ip: str = "127.0.0.1") -> dict:
    profile_type = data.get("profile_type", "other")
    if profile_type not in ["acne", "eczema", "psoriasis", "other"]:
        raise ValidationException("profile_type không hợp lệ")

    body_site = data.get("body_site", "other")
    title = data.get("title", f"Theo dõi vùng da {body_site}")
    diagnosis_status = data.get("diagnosis_status", "unknown")

    case_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db = get_db()

    db.execute(
        """
        INSERT INTO cases (id, patient_id, profile_type, diagnosis_status, title, body_site, status, cadence_days, is_synthetic, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'active', 7, 0, ?, ?)
        """,
        (case_id, user_id, profile_type, diagnosis_status, title, body_site, now, now)
    )
    db.commit()

    record_audit_event(user_id, "patient", "create_case", "case", case_id, "allow", ip)
    return {
        "id": case_id,
        "patient_id": user_id,
        "profile_type": profile_type,
        "diagnosis_status": diagnosis_status,
        "title": title,
        "body_site": body_site,
        "status": "active",
        "created_at": now
    }

def get_case(user_id: str, case_id: str, ip: str = "127.0.0.1") -> dict:
    case = check_patient_owns_case(user_id, case_id, ip)
    record_audit_event(user_id, "patient", "view_case", "case", case_id, "allow", ip)
    return case

def list_user_cases(user_id: str, ip: str = "127.0.0.1") -> list:
    db = get_db()
    rows = db.execute("SELECT * FROM cases WHERE patient_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    record_audit_event(user_id, "patient", "list_cases", "case", "all", "allow", ip)
    return [dict(r) for r in rows]

def close_case(user_id: str, case_id: str, ip: str = "127.0.0.1") -> dict:
    check_patient_owns_case(user_id, case_id, ip)
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute("UPDATE cases SET status = 'closed', updated_at = ? WHERE id = ?", (now, case_id))
    db.commit()
    record_audit_event(user_id, "patient", "close_case", "case", case_id, "allow", ip)
    return {"status": "closed", "case_id": case_id}

def create_observation(user_id: str, case_id: str, data: dict = None, ip: str = "127.0.0.1") -> dict:
    check_patient_owns_case(user_id, case_id, ip)
    data = data or {}
    obs_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    notes = data.get("notes", "")

    db = get_db()
    db.execute(
        """
        INSERT INTO observations (id, case_id, captured_at, workflow_state, quality_status, notes, created_at, updated_at)
        VALUES (?, ?, ?, 'DRAFT', NULL, ?, ?, ?)
        """,
        (obs_id, case_id, now, notes, now, now)
    )
    db.commit()

    record_audit_event(user_id, "patient", "create_observation", "observation", obs_id, "allow", ip)
    return {
        "id": obs_id,
        "case_id": case_id,
        "captured_at": now,
        "workflow_state": "DRAFT",
        "notes": notes
    }

def update_observation_state(obs_id: str, target_state: str, quality_status: str = None) -> dict:
    db = get_db()
    obs = db.execute("SELECT * FROM observations WHERE id = ?", (obs_id,)).fetchone()
    if not obs:
        raise NotFoundException("Quan sát không tồn tại")

    curr_state = obs["workflow_state"]
    new_state = transition(curr_state, target_state)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if quality_status:
        db.execute(
            "UPDATE observations SET workflow_state = ?, quality_status = ?, updated_at = ? WHERE id = ?",
            (new_state, quality_status, now, obs_id)
        )
    else:
        db.execute(
            "UPDATE observations SET workflow_state = ?, updated_at = ? WHERE id = ?",
            (new_state, now, obs_id)
        )
    db.commit()
    return {"id": obs_id, "workflow_state": new_state, "quality_status": quality_status or obs["quality_status"]}

def add_symptoms(user_id: str, case_id: str, data: dict, ip: str = "127.0.0.1") -> dict:
    check_patient_owns_case(user_id, case_id, ip)
    form_version = data.get("form_version", "v1.0")
    answers = data.get("answers", {})
    recall_window_days = data.get("recall_window_days", 7)

    symptom_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db = get_db()

    db.execute(
        """
        INSERT INTO symptom_entries (id, case_id, entered_at, form_version, answers, recall_window_days, provenance, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'user_reported', ?, ?)
        """,
        (symptom_id, case_id, now, form_version, json.dumps(answers), recall_window_days, now, now)
    )
    db.commit()

    record_audit_event(user_id, "patient", "add_symptoms", "symptom_entry", symptom_id, "allow", ip)
    return {
        "id": symptom_id,
        "case_id": case_id,
        "entered_at": now,
        "provenance": "user_reported",
        "answers": answers
    }

def get_case_symptoms(user_id: str, case_id: str, ip: str = "127.0.0.1") -> list:
    check_patient_owns_case(user_id, case_id, ip)
    db = get_db()
    rows = db.execute("SELECT * FROM symptom_entries WHERE case_id = ? ORDER BY entered_at DESC", (case_id,)).fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["answers"] = json.loads(d["answers"]) if isinstance(d["answers"], str) else d["answers"]
        res.append(d)
    record_audit_event(user_id, "patient", "list_symptoms", "symptom_entry", case_id, "allow", ip)
    return res
