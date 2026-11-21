"""
consults.py router — Doctor-Patient Text Consultation Messaging.
Rules:
- Audited access.
- Requires active, non-expired, non-revoked consent.
- Messages are text-only.
"""
import uuid
import datetime
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.errors import ForbiddenException, ConsentRequiredException, NotFoundException

def send_consult_message(user_id: str, consent_id: str, body: str, ip: str = "127.0.0.1") -> dict:
    body = body.strip()
    if not body:
        raise ValueError("Nội dung tin nhắn không được để trống")

    db = get_db()
    c = db.execute(
        """
        SELECT c.*, cp.user_id as doctor_user_id
        FROM consents c
        LEFT JOIN clinician_profiles cp ON c.recipient_clinic_id = cp.clinic_id
        WHERE c.id = ?
        """,
        (consent_id,)
    ).fetchone()

    if not c:
        raise NotFoundException("Consent không tồn tại")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if c["status"] != "active" or c["expires_at"] < now_iso:
        record_audit_event(user_id, "user", "send_consult_message", "consent", consent_id, "deny", ip)
        raise ConsentRequiredException("Consent đã hết hạn hoặc bị thu hồi")

    # Verify sender is either patient or clinic doctor
    if user_id != c["patient_id"] and user_id != c["doctor_user_id"]:
        record_audit_event(user_id, "user", "send_consult_message", "consent", consent_id, "deny", ip)
        raise ForbiddenException("Bạn không phải thành viên của cuộc tư vấn này")

    msg_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO consult_messages (id, consent_id, sender_id, body, sent_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (msg_id, consent_id, user_id, body, now_iso, now_iso, now_iso)
    )
    db.commit()

    record_audit_event(user_id, "user", "send_consult_message", "consult_message", msg_id, "allow", ip)

    return {
        "id": msg_id,
        "consent_id": consent_id,
        "sender_id": user_id,
        "sent_at": now_iso
    }

def get_consult_messages(user_id: str, consent_id: str, ip: str = "127.0.0.1") -> list:
    db = get_db()
    c = db.execute(
        """
        SELECT c.*, cp.user_id as doctor_user_id
        FROM consents c
        LEFT JOIN clinician_profiles cp ON c.recipient_clinic_id = cp.clinic_id
        WHERE c.id = ?
        """,
        (consent_id,)
    ).fetchone()

    if not c:
        raise NotFoundException("Consent không tồn tại")

    if user_id != c["patient_id"] and user_id != c["doctor_user_id"]:
        record_audit_event(user_id, "user", "get_consult_messages", "consent", consent_id, "deny", ip)
        raise ForbiddenException("Bạn không có quyền xem cuộc tư vấn này")

    rows = db.execute(
        """
        SELECT cm.*, u.display_name as sender_name, u.role as sender_role
        FROM consult_messages cm
        JOIN users u ON cm.sender_id = u.id
        WHERE cm.consent_id = ?
        ORDER BY cm.sent_at ASC
        """,
        (consent_id,)
    ).fetchall()

    record_audit_event(user_id, "user", "get_consult_messages", "consult_message", consent_id, "allow", ip)
    return [dict(r) for r in rows]
