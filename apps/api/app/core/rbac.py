"""
rbac.py — Role-Based Access Control and Consent Enforcement.
Enforces Section 7 matrix:
- Patient: CRUD own cases/observations/symptoms/consents.
- Clinician: can view case/images/symptoms ONLY IF active consent exists, within expiration,
  within scope, clinician is verified, clinic is verified, and Partner subscription is active!
- Admin: view audits, verify clinics/clinicians, user management.
Any violation immediately raises ForbiddenException or ConsentRequiredException / ConsentExpiredException
and logs an audit event with result="deny".
"""
import datetime
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.errors import ForbiddenException, ConsentRequiredException, ConsentExpiredException, PartnerRequiredException

def check_patient_owns_case(user_id: str, case_id: str, ip: str = "127.0.0.1") -> dict:
    """Verify that user is the owner of the case."""
    db = get_db()
    row = db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if not row:
        record_audit_event(user_id, "patient", "view_case", "case", case_id, "deny", ip)
        raise ForbiddenException("Hồ sơ ca không tồn tại")
    if row["patient_id"] != user_id:
        record_audit_event(user_id, "patient", "view_case", "case", case_id, "deny", ip)
        raise ForbiddenException("Bạn không phải chủ sở hữu của hồ sơ này")
    return dict(row)

def check_clinician_has_consent(
    clinician_id: str,
    case_id: str,
    required_scope_item: str = None,  # 'images', 'measurements', 'symptoms', 'reports'
    ip: str = "127.0.0.1"
) -> dict:
    """
    Verify clinician access rights:
    1. Clinician profile is verified.
    2. Clinician belongs to a verified clinic.
    3. Clinic has an active Partner subscription (partner_until > now).
    4. Active consent exists for this clinic/case, not revoked, not expired.
    5. Required scope item is granted.
    """
    db = get_db()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1 & 2. Check clinician profile & clinic
    clinician_prof = db.execute(
        """
        SELECT cp.*, c.verification_status as clinic_verif, c.partner_until, c.name as clinic_name
        FROM clinician_profiles cp
        JOIN clinics c ON cp.clinic_id = c.id
        WHERE cp.user_id = ?
        """,
        (clinician_id,)
    ).fetchone()

    if not clinician_prof:
        record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
        raise ForbiddenException("Bác sĩ chưa liên kết với phòng khám nào")

    if clinician_prof["verification_status"] != "verified":
        record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
        raise ForbiddenException("Chứng chỉ bác sĩ đang chờ admin phê duyệt")

    if clinician_prof["clinic_verif"] != "verified":
        record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
        raise ForbiddenException("Phòng khám chưa được admin phê duyệt")

    # 3. Check Verified Partner status
    partner_until = clinician_prof["partner_until"]
    if not partner_until or partner_until < now_iso:
        record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
        raise PartnerRequiredException("Gói Verified Partner của phòng khám đã hết hạn")

    clinic_id = clinician_prof["clinic_id"]

    # 4. Check consent
    consent = db.execute(
        """
        SELECT * FROM consents
        WHERE case_id = ? AND recipient_clinic_id = ?
        ORDER BY created_at DESC LIMIT 1
        """,
        (case_id, clinic_id)
    ).fetchone()

    if not consent:
        record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
        raise ConsentRequiredException("Chưa có sự đồng ý (consent) từ bệnh nhân cho phòng khám này")

    if consent["status"] == "revoked":
        record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
        raise ConsentExpiredException("Bệnh nhân đã thu hồi quyền truy cập hồ sơ này")

    if consent["status"] == "expired" or consent["expires_at"] < now_iso:
        record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
        raise ConsentExpiredException("Quyền truy cập consent đã hết hạn")

    # 5. Check scope
    if required_scope_item:
        import json
        scope = json.loads(consent["scope"]) if isinstance(consent["scope"], str) else consent["scope"]
        if not scope.get(required_scope_item, False):
            record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "deny", ip)
            raise ForbiddenException(f"Bệnh nhân không cấp quyền truy cập {required_scope_item}")

    record_audit_event(clinician_id, "clinician", "view_case", "case", case_id, "allow", ip)
    return dict(consent)

def enforce_admin(arg1: str, arg2: str = None, arg3: str = None, ip: str = "127.0.0.1"):
    """
    Verify admin role.
    Supports:
    - enforce_admin(admin_id, action, [ip]): looks up admin_id in DB, requires role == 'admin' and status == 'active'.
    - enforce_admin(role, user_id, action, [ip]): validates role == 'admin' and checks DB if user exists.
    """
    db = get_db()
    if arg1 in ("admin", "patient", "clinician"):
        # Called as (role, user_id, action, [ip])
        role = arg1
        user_id = arg2
        act = arg3 or "admin_action"
        if role != "admin":
            record_audit_event(user_id, role, act, "admin_resource", "all", "deny", ip)
            raise ForbiddenException("Yêu cầu quyền Quản trị viên (Admin)")
        row = db.execute("SELECT role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        if row and (row["role"] != "admin" or row["status"] != "active"):
            record_audit_event(user_id, row["role"], act, "admin_resource", "all", "deny", ip)
            raise ForbiddenException("Yêu cầu quyền Quản trị viên (Admin)")
        record_audit_event(user_id, "admin", act, "admin_resource", "all", "allow", ip)
    else:
        # Called as (admin_id, action, [ip])
        user_id = arg1
        act = arg2 or "admin_action"
        if arg3 and ("." in str(arg3) or ":" in str(arg3)):
            ip = str(arg3)
        row = db.execute("SELECT role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or row["role"] != "admin" or row["status"] != "active":
            actual_role = row["role"] if row else "unknown"
            record_audit_event(user_id, actual_role, act, "admin_resource", "all", "deny", ip)
            raise ForbiddenException("Yêu cầu quyền Quản trị viên (Admin)")
        record_audit_event(user_id, "admin", act, "admin_resource", "all", "allow", ip)
