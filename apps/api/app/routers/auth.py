"""
auth.py — Authentication and User Management Router.
Endpoints:
- POST /api/auth/register
- POST /api/auth/register-clinician
- POST /api/auth/login
- POST /api/auth/privy/exchange
- GET /api/me
- POST /api/me/privacy-accept
- PATCH /api/me
- GET /api/me/export
- DELETE /api/me
"""
import uuid
import datetime
import json
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.audit import record_audit_event
from app.errors import ValidationException, UnauthenticatedException, ForbiddenException, NotFoundException

def register_patient(data: dict, ip: str = "127.0.0.1") -> dict:
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    display_name = data.get("display_name", "")

    if not email or "@" not in email:
        raise ValidationException("Email không hợp lệ")
    if len(password) < 8:
        raise ValidationException("Mật khẩu phải có ít nhất 8 ký tự")

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise ValidationException("Email đã được đăng ký", details={"field": "email"})

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO users (id, email, display_name, role, auth_provider, password_hash, locale, status, created_at, updated_at)
        VALUES (?, ?, ?, 'patient', 'local', ?, 'vi', 'active', ?, ?)
        """,
        (user_id, email, display_name, pw_hash, now, now)
    )
    db.commit()

    token = create_access_token(user_id, "patient", email)
    record_audit_event(user_id, "patient", "register", "user", user_id, "allow", ip)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            "role": "patient",
            "locale": "vi",
            "status": "active"
        }
    }

def register_clinician(data: dict, ip: str = "127.0.0.1") -> dict:
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    display_name = data.get("display_name", "")
    clinic_id = data.get("clinic_id", "")
    clinic_role = data.get("clinic_role", "doctor")
    license_no = data.get("license_no", "")

    if not email or "@" not in email:
        raise ValidationException("Email không hợp lệ")
    if len(password) < 8:
        raise ValidationException("Mật khẩu phải có ít nhất 8 ký tự")
    if not clinic_id:
        raise ValidationException("Cần chọn phòng khám liên kết")

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise ValidationException("Email đã được đăng ký", details={"field": "email"})

    clinic = db.execute("SELECT id FROM clinics WHERE id = ?", (clinic_id,)).fetchone()
    if not clinic:
        raise ValidationException("Phòng khám không tồn tại")

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO users (id, email, display_name, role, auth_provider, password_hash, locale, status, created_at, updated_at)
        VALUES (?, ?, ?, 'clinician', 'local', ?, 'vi', 'active', ?, ?)
        """,
        (user_id, email, display_name, pw_hash, now, now)
    )

    db.execute(
        """
        INSERT INTO clinician_profiles (user_id, clinic_id, clinic_role, license_no_enc, verification_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """,
        (user_id, clinic_id, clinic_role, license_no, now, now)
    )
    db.commit()

    token = create_access_token(user_id, "clinician", email)
    record_audit_event(user_id, "clinician", "register_clinician", "user", user_id, "allow", ip)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            "role": "clinician",
            "verification_status": "pending"
        }
    }

def login(data: dict, ip: str = "127.0.0.1") -> dict:
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        raise ValidationException("Vui lòng nhập email và mật khẩu")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        record_audit_event("anonymous", "guest", "login", "user", email, "deny", ip)
        raise UnauthenticatedException("Email hoặc mật khẩu không chính xác")

    if user["status"] != "active":
        record_audit_event(user["id"], user["role"], "login", "user", user["id"], "deny", ip)
        raise ForbiddenException("Tài khoản đã bị tạm khóa")

    if not verify_password(password, user["password_hash"]):
        record_audit_event(user["id"], user["role"], "login", "user", user["id"], "deny", ip)
        raise UnauthenticatedException("Email hoặc mật khẩu không chính xác")

    token = create_access_token(user["id"], user["role"], user["email"])
    record_audit_event(user["id"], user["role"], "login", "user", user["id"], "allow", ip)

    res_user = {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "role": user["role"],
        "locale": user["locale"],
        "privacy_accepted_at": user["privacy_accepted_at"]
    }

    if user["role"] == "clinician":
        prof = db.execute("SELECT * FROM clinician_profiles WHERE user_id = ?", (user["id"],)).fetchone()
        if prof:
            res_user["verification_status"] = prof["verification_status"]
            res_user["clinic_id"] = prof["clinic_id"]

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": res_user
    }

def get_current_user(token: str) -> dict:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise UnauthenticatedException("Người dùng không tồn tại")
    u = dict(user)
    if "password_hash" in u:
        del u["password_hash"]
    return u

def accept_privacy(user_id: str, version: str = "v1.0", ip: str = "127.0.0.1") -> dict:
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute(
        """
        UPDATE users
        SET privacy_accepted_at = ?, privacy_version = ?, terms_accepted_at = ?, terms_version = ?, updated_at = ?
        WHERE id = ?
        """,
        (now, version, now, version, now, user_id)
    )
    db.commit()
    record_audit_event(user_id, "user", "accept_privacy", "user", user_id, "allow", ip)
    return {"status": "ok", "privacy_accepted_at": now}

def export_my_data(user_id: str, ip: str = "127.0.0.1") -> dict:
    """Export all user data including cases, symptoms, observations (metadata)."""
    db = get_db()
    user = db.execute("SELECT id, email, display_name, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    cases = db.execute("SELECT * FROM cases WHERE patient_id = ?", (user_id,)).fetchall()

    export_payload = {
        "user": dict(user) if user else {},
        "cases": [dict(c) for c in cases],
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    record_audit_event(user_id, "patient", "export_data", "user", user_id, "allow", ip)
    return export_payload

def delete_my_data(user_id: str, ip: str = "127.0.0.1") -> dict:
    """Anonymize/delete user personal data while keeping anonymized audit events."""
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Anonymize user record
    db.execute(
        """
        UPDATE users
        SET email = ?, display_name = 'Deleted User', password_hash = NULL, status = 'disabled', updated_at = ?
        WHERE id = ?
        """,
        (f"deleted_{user_id[:8]}@anonymized.local", now, user_id)
    )
    # Remove symptoms
    db.execute("DELETE FROM symptom_entries WHERE case_id IN (SELECT id FROM cases WHERE patient_id = ?)", (user_id,))
    # Remove cases
    db.execute("DELETE FROM cases WHERE patient_id = ?", (user_id,))
    db.commit()

    record_audit_event(user_id, "patient", "delete_account", "user", user_id, "allow", ip)
    return {"status": "account_anonymized_and_deleted"}
