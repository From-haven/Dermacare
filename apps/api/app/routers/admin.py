"""
admin.py router — Admin Management, Verifications, and Audit Log Viewer.
"""
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.core.rbac import enforce_admin
from app.errors import NotFoundException
import datetime

def list_pending_clinicians(admin_id: str, ip: str = "127.0.0.1") -> list:
    enforce_admin(admin_id, "list_pending_clinicians", ip)
    db = get_db()
    rows = db.execute(
        """
        SELECT cp.*, u.email, u.display_name, c.name as clinic_name
        FROM clinician_profiles cp
        JOIN users u ON cp.user_id = u.id
        JOIN clinics c ON cp.clinic_id = c.id
        WHERE cp.verification_status = 'pending'
        """
    ).fetchall()
    return [dict(r) for r in rows]

def verify_clinician(admin_id: str, clinician_user_id: str, action: str = "verified", ip: str = "127.0.0.1") -> dict:
    enforce_admin(admin_id, "verify_clinician", ip)
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute(
        """
        UPDATE clinician_profiles
        SET verification_status = ?, verified_by = ?, verified_at = ?, updated_at = ?
        WHERE user_id = ?
        """,
        (action, admin_id, now, now, clinician_user_id)
    )
    db.commit()
    record_audit_event(admin_id, "admin", "verify_clinician", "user", clinician_user_id, "allow", ip)
    return {"user_id": clinician_user_id, "verification_status": action}

def verify_clinic(admin_id: str, clinic_id: str, action: str = "verified", ip: str = "127.0.0.1") -> dict:
    enforce_admin(admin_id, "verify_clinic", ip)
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute(
        "UPDATE clinics SET verification_status = ?, updated_at = ? WHERE id = ?",
        (action, now, clinic_id)
    )
    db.commit()
    record_audit_event(admin_id, "admin", "verify_clinic", "clinic", clinic_id, "allow", ip)
    return {"clinic_id": clinic_id, "verification_status": action}

def get_audit_logs(admin_id: str, limit: int = 50, ip: str = "127.0.0.1") -> list:
    enforce_admin(admin_id, "view_audit_logs", ip)
    db = get_db()
    rows = db.execute("SELECT * FROM audit_events ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

def get_system_health(admin_id: str = None) -> dict:
    """System health check (zero secrets exposed)."""
    db = get_db()
    db_ok = True
    try:
        db.execute("SELECT 1").fetchone()
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "error",
        "vision_engine": "operational",
        "chain_mode": "mock",
        "auth_mode": "local",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
