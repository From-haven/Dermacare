"""
images.py — Router for Image Upload, Processing, Quality Gate, and Encrypted Content Retrieval.
Enforces:
- MIME & magic bytes verification
- EXIF stripping via Pillow re-encode
- Duplicate sha256 check (T03)
- Quality assessment gate (T01)
- Privacy acceptance check before upload (T04)
- Envelope encryption at rest (AES-256-GCM + DEK)
- Short-lived 60-second token access
"""
import uuid
import datetime
import io
from PIL import Image
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.core.crypto import encrypt_image_bytes, decrypt_image_bytes
from app.core.security import create_image_token, verify_image_token
from app.core.storage import save_encrypted_asset, get_encrypted_asset, compute_sha256, compute_phash
from app.services.state_machine import transition
from ml.vision.quality import assess_image_quality
from app.errors import ValidationException, DuplicateImageException, ForbiddenException, NotFoundException, UnauthenticatedException

MAGIC_BYTES = {
    b"\xFF\xD8\xFF": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp"
}

def strip_exif(raw_bytes: bytes) -> tuple:
    """Re-encode image cleanly with Pillow to strip all EXIF / GPS / device metadata."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        # Convert to RGB (dropping RGBA / P palette transparency issues if any)
        clean_img = Image.new("RGB", img.size)
        clean_img.paste(img)
        buf = io.BytesIO()
        clean_img.save(buf, format="JPEG", quality=92)
        clean_bytes = buf.getvalue()
        return clean_bytes, img.size[0], img.size[1]
    except Exception as e:
        raise ValidationException("Không thể đọc định dạng hình ảnh", details={"error": str(e)})

def upload_observation_image(user_id: str, observation_id: str, raw_bytes: bytes, view_type: str = "overview", ip: str = "127.0.0.1") -> dict:
    """
    Handle image upload:
    1. Check privacy acceptance (T04).
    2. Validate size and magic bytes.
    3. Duplicate check (T03).
    4. Strip EXIF metadata.
    5. Run Quality Gate (T01).
    6. Encrypt with AES-256-GCM + DEK and store.
    7. Update observation state.
    """
    db = get_db()

    # 1. T04: Privacy acceptance enforcement
    user = db.execute("SELECT privacy_accepted_at FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or not user["privacy_accepted_at"]:
        record_audit_event(user_id, "patient", "upload_image", "image", "new", "deny", ip)
        raise ForbiddenException("Bạn cần đọc và chấp nhận Điều khoản & Chính sách quyền riêng tư trước khi tải ảnh")

    # Check observation exists
    obs = db.execute("SELECT * FROM observations WHERE id = ?", (observation_id,)).fetchone()
    if not obs:
        raise NotFoundException("Quan sát không tồn tại")

    # 2. File size & MIME verification
    if len(raw_bytes) > 12 * 1024 * 1024:
        raise ValidationException("Ảnh vượt quá kích thước cho phép (tối đa 12MB)")

    is_valid_magic = any(raw_bytes.startswith(magic) for magic in MAGIC_BYTES)
    if not is_valid_magic:
        raise ValidationException("Định dạng file không được hỗ trợ (chỉ nhận JPEG, PNG, WEBP)")

    # 3. T03: Duplicate image check via SHA256
    sha256_hash = compute_sha256(raw_bytes)
    existing = db.execute("SELECT id FROM image_assets WHERE sha256 = ?", (sha256_hash,)).fetchone()
    if existing:
        record_audit_event(user_id, "patient", "upload_image", "image", sha256_hash, "deny", ip)
        raise DuplicateImageException("Ảnh đã tồn tại trong hệ thống (trùng lặp hoàn toàn)")

    # 4. Strip EXIF
    clean_bytes, width, height = strip_exif(raw_bytes)
    phash = compute_phash(clean_bytes)

    # 5. Quality Gate
    q_result = assess_image_quality(clean_bytes)
    quality_status = q_result["status"]  # PASS | RETAKE | REVIEW

    # 6. Envelope Encryption
    encrypted_bytes, wrapped_dek_b64 = encrypt_image_bytes(clean_bytes)
    image_id = str(uuid.uuid4())
    object_key = f"images/{user_id[:8]}/{image_id}.enc"
    save_encrypted_asset(object_key, encrypted_bytes)

    # Database records
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute(
        """
        INSERT INTO image_assets (id, observation_id, view_type, object_key, sha256, phash, mime, width, height, dek_wrapped, exif_stripped, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'image/jpeg', ?, ?, ?, 1, ?, ?)
        """,
        (image_id, observation_id, view_type, object_key, sha256_hash, phash, width, height, wrapped_dek_b64, now, now)
    )

    q_id = str(uuid.uuid4())
    import json
    db.execute(
        """
        INSERT INTO quality_reports (id, image_id, status, metrics, reasons, thresholds_version, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (q_id, image_id, quality_status, json.dumps(q_result["metrics"]), json.dumps(q_result["reasons"]), q_result["thresholds_version"], now, now)
    )

    # 7. Update observation workflow state
    target_state = "READY_FOR_ANALYSIS" if quality_status == "PASS" else "QUALITY_REJECTED"
    try:
        new_state = transition(obs["workflow_state"], target_state)
    except Exception:
        new_state = target_state

    db.execute(
        "UPDATE observations SET workflow_state = ?, quality_status = ?, updated_at = ? WHERE id = ?",
        (new_state, quality_status, now, observation_id)
    )
    db.commit()

    record_audit_event(user_id, "patient", "upload_image", "image", image_id, "allow", ip)

    return {
        "image_id": image_id,
        "observation_id": observation_id,
        "quality_status": quality_status,
        "quality_report": q_result,
        "width": width,
        "height": height,
        "workflow_state": new_state
    }

def request_image_token(user_id: str, image_id: str, ip: str = "127.0.0.1") -> dict:
    """
    Generate short-lived 60-second token for viewing encrypted image.
    Enforces Section 7 & Fix-06:
    - Patient: must be case owner.
    - Clinician: must have active consent with 'images' scope and active partner clinic.
    - Admin: 403 Forbidden (Admin never accesses raw medical images).
    """
    db = get_db()
    row = db.execute(
        """
        SELECT ia.*, o.case_id, c.patient_id
        FROM image_assets ia
        JOIN observations o ON ia.observation_id = o.id
        JOIN cases c ON o.case_id = c.id
        WHERE ia.id = ?
        """,
        (image_id,)
    ).fetchone()
    if not row:
        raise NotFoundException("Ảnh không tồn tại")

    user_row = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    user_role = user_row["role"] if user_row else "patient"

    if user_role == "admin":
        record_audit_event(user_id, "admin", "request_image_token", "image", image_id, "deny", ip)
        raise ForbiddenException("Quản trị viên không được phép truy cập hình ảnh y tế")

    if user_role == "patient":
        if row["patient_id"] != user_id:
            record_audit_event(user_id, "patient", "request_image_token", "image", image_id, "deny", ip)
            raise ForbiddenException("Bạn không có quyền xem ảnh của hồ sơ này")
    elif user_role == "clinician":
        from app.core.rbac import check_clinician_has_consent
        check_clinician_has_consent(user_id, row["case_id"], required_scope_item="images", ip=ip)
    else:
        record_audit_event(user_id, user_role, "request_image_token", "image", image_id, "deny", ip)
        raise ForbiddenException("Không có quyền truy cập ảnh")

    token = create_image_token(image_id, user_id, lifetime_seconds=60)
    record_audit_event(user_id, user_role, "request_image_token", "image", image_id, "allow", ip)
    return {"image_id": image_id, "token": token, "expires_in_seconds": 60}

def get_image_content(image_id: str, token: str, ip: str = "127.0.0.1") -> tuple:
    """
    Retrieve and decrypt image bytes using short-lived 60-second token.
    Returns: (clean_bytes, mime_type)
    """
    user_id = verify_image_token(token, image_id)
    db = get_db()
    img = db.execute("SELECT * FROM image_assets WHERE id = ?", (image_id,)).fetchone()
    if not img:
        raise NotFoundException("Ảnh không tồn tại")

    encrypted_bytes = get_encrypted_asset(img["object_key"])
    clean_bytes = decrypt_image_bytes(encrypted_bytes, img["dek_wrapped"])

    record_audit_event(user_id, "user", "view_image_content", "image", image_id, "allow", ip)
    return clean_bytes, img["mime"]
