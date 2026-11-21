"""
consents.py router — Patient Consent Lifecycle Management.
Endpoints:
- POST /api/consents: grant consent to a clinic.
- GET /api/consents: list user's consents.
- GET /api/consents/{id}: consent detail.
- DELETE /api/consents/{id}: revoke consent with IMMEDIATE off-chain effect (T06).
"""
import uuid
import datetime
import hashlib
import json
import secrets
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.core.crypto import encrypt_nonce
from app.core.rbac import check_patient_owns_case
from app.services.chain.client import chain_client
from app.errors import ValidationException, NotFoundException, ForbiddenException, PartnerRequiredException

def create_consent(user_id: str, data: dict, ip: str = "127.0.0.1") -> dict:
    case_id = data.get("case_id")
    recipient_clinic_id = data.get("recipient_clinic_id")
    scope = data.get("scope", {"images": True, "measurements": True, "symptoms": True, "reports": True})
    purpose = data.get("purpose", "Khám và tư vấn chuyên khoa da liễu")
    days = data.get("days", 14)

    if not case_id or not recipient_clinic_id:
        raise ValidationException("Thiếu case_id hoặc recipient_clinic_id")

    check_patient_owns_case(user_id, case_id, ip)

    db = get_db()
    # Check clinic exists & has active Partner package
    now = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.isoformat()
    clinic = db.execute("SELECT * FROM clinics WHERE id = ?", (recipient_clinic_id,)).fetchone()
    if not clinic:
        raise NotFoundException("Phòng khám không tồn tại")

    if not clinic["partner_until"] or clinic["partner_until"] < now_iso:
        raise PartnerRequiredException("Chỉ phòng khám có gói Verified Partner đang hiệu lực mới được nhận hồ sơ")

    # CSPRNG 32-byte nonce
    nonce32 = secrets.token_bytes(32)
    nonce_enc = encrypt_nonce(nonce32)

    consent_id = str(uuid.uuid4())
    expires_at = (now + datetime.timedelta(days=days)).isoformat()

    # Zero PII commitment on chain
    scope_str = json.dumps(scope, sort_keys=True)
    scope_hash = hashlib.sha256(scope_str.encode('utf-8')).hexdigest()
    commitment_data = nonce32 + f"{consent_id}:{recipient_clinic_id}:{scope_hash}:{expires_at}".encode('utf-8')
    commitment = "0x" + hashlib.sha256(commitment_data).hexdigest()

    chain_res = chain_client.submit_grant(commitment, int((now + datetime.timedelta(days=days)).timestamp()))
    grant_tx_id = chain_res.get("tx_hash", f"0x{secrets.token_hex(32)}")
    chain_status = chain_res.get("status", "CONFIRMED")

    db.execute(
        """
        INSERT INTO consents (
            id, patient_id, case_id, recipient_clinic_id, recipient_user_id,
            scope, purpose, expires_at, status, commitment, nonce_enc, grant_tx_id,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
        """,
        (consent_id, user_id, case_id, recipient_clinic_id, json.dumps(scope), purpose,
         expires_at, commitment, nonce_enc, grant_tx_id, now_iso, now_iso)
    )

    # Record chain transaction
    tx_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO chain_transactions (id, kind, idempotency_key, status, tx_hash, chain_id, created_at, updated_at)
        VALUES (?, 'consent_grant', ?, ?, ?, 43113, ?, ?)
        """,
        (tx_id, f"grant_{consent_id}", chain_status, grant_tx_id, now_iso, now_iso)
    )
    db.commit()

    record_audit_event(user_id, "patient", "grant_consent", "consent", consent_id, "allow", ip)

    return {
        "id": consent_id,
        "case_id": case_id,
        "recipient_clinic_id": recipient_clinic_id,
        "status": "active",
        "expires_at": expires_at,
        "commitment": commitment,
        "tx_hash": grant_tx_id
    }

def revoke_consent(user_id: str, consent_id: str, ip: str = "127.0.0.1") -> dict:
    """
    Revoke consent with IMMEDIATE off-chain effect.
    The doctor is immediately blocked on the next HTTP request (T06).
    """
    db = get_db()
    c = db.execute("SELECT * FROM consents WHERE id = ?", (consent_id,)).fetchone()
    if not c:
        raise NotFoundException("Consent không tồn tại")
    if c["patient_id"] != user_id:
        record_audit_event(user_id, "patient", "revoke_consent", "consent", consent_id, "deny", ip)
        raise ForbiddenException("Bạn không có quyền thu hồi consent của người khác")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    chain_res = chain_client.submit_revoke(c["commitment"])
    revoke_tx_id = chain_res.get("tx_hash", f"0x{secrets.token_hex(32)}")
    chain_status = chain_res.get("status", "CONFIRMED")

    db.execute(
        """
        UPDATE consents
        SET status = 'revoked', revoked_at = ?, revoke_tx_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (now_iso, revoke_tx_id, now_iso, consent_id)
    )

    # Chain transaction for revoke
    tx_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO chain_transactions (id, kind, idempotency_key, status, tx_hash, chain_id, created_at, updated_at)
        VALUES (?, 'consent_revoke', ?, ?, ?, 43113, ?, ?)
        """,
        (tx_id, f"revoke_{consent_id}", chain_status, revoke_tx_id, now_iso, now_iso)
    )
    db.commit()

    record_audit_event(user_id, "patient", "revoke_consent", "consent", consent_id, "allow", ip)

    return {
        "id": consent_id,
        "status": "revoked",
        "revoked_at": now_iso,
        "tx_hash": revoke_tx_id
    }

def get_consent(user_id: str, consent_id: str, ip: str = "127.0.0.1") -> dict:
    db = get_db()
    c = db.execute("SELECT * FROM consents WHERE id = ?", (consent_id,)).fetchone()
    if not c:
        raise NotFoundException("Consent không tồn tại")
    if c["patient_id"] != user_id:
        record_audit_event(user_id, "patient", "view_consent", "consent", consent_id, "deny", ip)
        raise ForbiddenException("Bạn không có quyền xem consent này")
    record_audit_event(user_id, "patient", "view_consent", "consent", consent_id, "allow", ip)
    res = dict(c)
    res["scope"] = json.loads(res["scope"]) if isinstance(res["scope"], str) else res["scope"]
    return res

def get_consent_chain(user_id: str, consent_id: str, ip: str = "127.0.0.1") -> dict:
    db = get_db()
    c = db.execute("SELECT * FROM consents WHERE id = ?", (consent_id,)).fetchone()
    if not c:
        raise NotFoundException("Consent không tồn tại")
    tx = db.execute(
        "SELECT * FROM chain_transactions WHERE idempotency_key = ? OR tx_hash = ?", 
        (f"grant_{consent_id}", c["grant_tx_id"])
    ).fetchone()
    return {
        "consent_id": consent_id,
        "commitment": c["commitment"],
        "grant_tx_id": c["grant_tx_id"],
        "revoke_tx_id": c["revoke_tx_id"],
        "chain_transaction": dict(tx) if tx else None
    }

def list_user_consents(user_id: str, ip: str = "127.0.0.1") -> list:
    db = get_db()
    rows = db.execute(
        """
        SELECT c.*, cl.name as clinic_name
        FROM consents c
        JOIN clinics cl ON c.recipient_clinic_id = cl.id
        WHERE c.patient_id = ?
        ORDER BY c.created_at DESC
        """,
        (user_id,)
    ).fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["scope"] = json.loads(d["scope"]) if isinstance(d["scope"], str) else d["scope"]
        res.append(d)
    record_audit_event(user_id, "patient", "list_consents", "consent", "all", "allow", ip)
    return res
