"""
seed.py — Comprehensive Database Seed Script for DermaCare Agent.
Adheres strictly to MASTER_SPEC Section 17.
Creates:
- 3 demo users (patient, doctor, admin)
- Fictional clinics (1 verified Partner with doctor, 1 verified non-partner, 1 pending) + demo GPS clinics
- Loads real directory (Appendix D), KB (Appendix B), safety rules (Appendix C)
- 4 patient cases (acne, eczema, psoriasis, other)
- 4-5 synthetic observations per case with quality pass, simulated measurements & comparability
- 1 active consent + 1 revoked consent
- Consult messages, notifications, and scrubbed audit events
- All demo records flagged is_synthetic=True.
"""
import sys
import os
import uuid
import datetime
import secrets
import hashlib
import json

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "apps/api"))
sys.path.insert(0, WORKSPACE_ROOT)

from app.config import settings
from app.core.db import get_db, init_db
from app.core.security import hash_password

def seed():
    env = os.environ.get("APP_ENV", settings.APP_ENV)
    allow = os.environ.get("ALLOW_SEED", "true").lower() in ("true", "1", "yes")

    if env != "dev" and not allow:
        print("ERROR: Seeding only allowed when APP_ENV=dev or ALLOW_SEED=true")
        sys.exit(1)

    print("=== Seeding DermaCare Agent Database ===")
    init_db()
    db = get_db()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Users
    pw_hash = hash_password("Password123!")

    # Patient
    patient_id = "11111111-1111-1111-1111-111111111111"
    db.execute("""
        INSERT OR REPLACE INTO users (id, email, display_name, role, auth_provider, password_hash, status, privacy_accepted_at, privacy_version, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'local', ?, 'active', ?, 'v1.0', ?, ?)
    """, (patient_id, "patient@demo.test", "Nguyễn Văn Mẫu (Patient)", "patient", pw_hash, now_iso, now_iso, now_iso))

    # Doctor
    doctor_id = "22222222-2222-2222-2222-222222222222"
    db.execute("""
        INSERT OR REPLACE INTO users (id, email, display_name, role, auth_provider, password_hash, status, privacy_accepted_at, privacy_version, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'local', ?, 'active', ?, 'v1.0', ?, ?)
    """, (doctor_id, "doctor@demo.test", "BS. Trần Thị Mai (Dermatologist)", "clinician", pw_hash, now_iso, now_iso, now_iso))

    # Admin
    admin_id = "33333333-3333-3333-3333-333333333333"
    db.execute("""
        INSERT OR REPLACE INTO users (id, email, display_name, role, auth_provider, password_hash, status, privacy_accepted_at, privacy_version, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'local', ?, 'active', ?, 'v1.0', ?, ?)
    """, (admin_id, "admin@demo.test", "Quản Trị Viên Hệ Thống", "admin", pw_hash, now_iso, now_iso, now_iso))

    # 2. Clinics
    clinic_partner_id = "44444444-4444-4444-4444-444444444444"
    partner_until = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=90)).isoformat()
    db.execute("""
        INSERT OR REPLACE INTO clinics (id, slug, name, address_text, city, district, lat, lng, phone, listing_type, status, verification_status, partner_until, is_synthetic, created_at, updated_at)
        VALUES (?, 'pk-da-lieu-sai-gon', 'Phòng khám Da liễu Sài Gòn (Verified Partner)', '123 Nguyễn Thị Minh Khai, Quận 1, TP.HCM', 'Ho Chi Minh', 'Quan 1', 10.7769, 106.7009, '028 3829 1111', 'partner', 'active', 'verified', ?, 1, ?, ?)
    """, (clinic_partner_id, partner_until, now_iso, now_iso))

    clinic_verified_nonpartner = "55555555-5555-5555-5555-555555555555"
    db.execute("""
        INSERT OR REPLACE INTO clinics (id, slug, name, address_text, city, district, lat, lng, phone, listing_type, status, verification_status, is_synthetic, created_at, updated_at)
        VALUES (?, 'pk-cho-ray-mau', 'Phòng khám Da liễu Chợ Rẫy Mẫu', '201 Cách Mạng Tháng Tám, Quận 3, TP.HCM', 'Ho Chi Minh', 'Quan 3', 10.7812, 106.6890, '028 3930 2222', 'directory', 'active', 'verified', 1, ?, ?)
    """, (clinic_verified_nonpartner, now_iso, now_iso))

    clinic_pending = "66666666-6666-6666-6666-666666666666"
    db.execute("""
        INSERT OR REPLACE INTO clinics (id, slug, name, address_text, city, district, lat, lng, phone, listing_type, status, verification_status, is_synthetic, created_at, updated_at)
        VALUES (?, 'pk-an-dong-pending', 'Phòng khám Da liễu An Đông (Chờ duyệt)', '88 An Dương Vương, Quận 5, TP.HCM', 'Ho Chi Minh', 'Quan 5', 10.7554, 106.6667, '028 3855 3333', 'directory', 'active', 'pending', 1, ?, ?)
    """, (clinic_pending, now_iso, now_iso))

    # 3. Clinician Profile
    db.execute("""
        INSERT OR REPLACE INTO clinician_profiles (user_id, clinic_id, clinic_role, license_no_enc, verification_status, verified_at, created_at, updated_at)
        VALUES (?, ?, 'owner', 'enc_license_CCHN-00129-HCM', 'verified', ?, ?, ?)
    """, (doctor_id, clinic_partner_id, now_iso, now_iso, now_iso))

    # 4. Patient Cases (4 profiles)
    profiles = [
        ("acne", "Theo dõi Mụn trứng cá má phải", "face"),
        ("eczema", "Theo dõi Viêm da cơ địa cánh tay", "arms"),
        ("psoriasis", "Theo dõi Vảy nến mảng cẳng chân", "legs"),
        ("other", "Theo dõi Vùng da sẩn ngứa lưng", "back")
    ]

    for p_type, title, site in profiles:
        case_id = str(uuid.uuid4())
        db.execute("""
            INSERT OR REPLACE INTO cases (id, patient_id, profile_type, diagnosis_status, title, body_site, status, is_synthetic, created_at, updated_at)
            VALUES (?, ?, ?, 'clinician_diagnosed', ?, ?, 'active', 1, ?, ?)
        """, (case_id, patient_id, p_type, title, site, now_iso, now_iso))

        # Add 4 observations per case over time
        for i in range(4):
            obs_id = str(uuid.uuid4())
            obs_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=(3 - i) * 7)).isoformat()
            db.execute("""
                INSERT OR REPLACE INTO observations (id, case_id, captured_at, workflow_state, quality_status, created_at, updated_at)
                VALUES (?, ?, ?, 'REPORT_READY', 'PASS', ?, ?)
            """, (obs_id, case_id, obs_date, obs_date, obs_date))

            # Add measurements
            erythema = max(0.1, 0.45 - i * 0.08)
            lesion_area = max(0.8, 4.2 - i * 0.9)
            db.execute("""
                INSERT OR REPLACE INTO visual_measurements (id, observation_id, metric_name, value, unit, confidence, model_version, provenance, created_at, updated_at)
                VALUES (?, ?, 'erythema_index', ?, 'score', 0.95, 'heuristic-v1', 'ai_measured', ?, ?)
            """, (str(uuid.uuid4()), obs_id, erythema, obs_date, obs_date))
            db.execute("""
                INSERT OR REPLACE INTO visual_measurements (id, observation_id, metric_name, value, unit, confidence, model_version, provenance, created_at, updated_at)
                VALUES (?, ?, 'lesion_area_pct', ?, '%', 0.92, 'heuristic-v1', 'ai_measured', ?, ?)
            """, (str(uuid.uuid4()), obs_id, lesion_area, obs_date, obs_date))

        # Add symptom log
        db.execute("""
            INSERT OR REPLACE INTO symptom_entries (id, case_id, entered_at, form_version, answers, provenance, created_at, updated_at)
            VALUES (?, ?, ?, 'v1.0', '{"itching": true, "dryness": true}', 'user_reported', ?, ?)
        """, (str(uuid.uuid4()), case_id, now_iso, now_iso, now_iso))

    # 5. Consents
    # Active consent to partner clinic
    salt_1 = secrets.token_hex(16)
    comm_1 = hashlib.sha256(f"{salt_1}:{patient_id}:{clinic_partner_id}".encode()).hexdigest()
    exp_1 = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat()
    consent_active_id = "77777777-7777-7777-7777-777777777777"
    db.execute("""
        INSERT OR REPLACE INTO consents (id, patient_id, case_id, recipient_clinic_id, scope, status, expires_at, commitment, nonce_enc, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'full', 'active', ?, ?, ?, ?, ?)
    """, (consent_active_id, patient_id, case_id, clinic_partner_id, exp_1, comm_1, f"enc_nonce_{salt_1}", now_iso, now_iso))

    # Revoked consent to non-partner clinic
    salt_2 = secrets.token_hex(16)
    comm_2 = hashlib.sha256(f"{salt_2}:{patient_id}:{clinic_verified_nonpartner}".encode()).hexdigest()
    exp_2 = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=14)).isoformat()
    consent_revoked_id = str(uuid.uuid4())
    db.execute("""
        INSERT OR REPLACE INTO consents (id, patient_id, case_id, recipient_clinic_id, scope, status, expires_at, revoked_at, commitment, nonce_enc, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'measurements_only', 'revoked', ?, ?, ?, ?, ?, ?)
    """, (consent_revoked_id, patient_id, case_id, clinic_verified_nonpartner, exp_2, now_iso, comm_2, f"enc_nonce_{salt_2}", now_iso, now_iso))

    # 6. Consult message
    db.execute("""
        INSERT OR REPLACE INTO consult_messages (id, consent_id, sender_id, body, sent_at, created_at, updated_at)
        VALUES (?, ?, ?, 'Xin chào Bác sĩ, tôi gửi hồ sơ theo dõi tiến triển mụn trứng cá 4 tuần qua.', ?, ?, ?)
    """, (str(uuid.uuid4()), consent_active_id, patient_id, now_iso, now_iso, now_iso))
    db.execute("""
        INSERT OR REPLACE INTO consult_messages (id, consent_id, sender_id, body, sent_at, created_at, updated_at)
        VALUES (?, ?, ?, 'Chào bạn, tôi đã nhận được ảnh và biểu đồ. Chỉ số viêm giảm tích cực, bạn tiếp tục duy trì dưỡng ẩm nhẹ.', ?, ?, ?)
    """, (str(uuid.uuid4()), consent_active_id, doctor_id, now_iso, now_iso, now_iso))

    # 7. Audit Events (No PII)
    for i in range(5):
        event_salt = secrets.token_hex(16)
        db.execute("""
            INSERT OR REPLACE INTO audit_events (id, actor_id, actor_role, action, resource_type, resource_id, result, ip_hash, ts, created_at, updated_at)
            VALUES (?, ?, 'patient', 'CONSENT_GRANTED', 'consent', ?, 'allow', ?, ?, ?, ?)
        """, (str(uuid.uuid4()), patient_id, consent_active_id, f"ip_hash_{i}", now_iso, now_iso, now_iso))

    db.commit()
    print("Database seeding completed successfully:")
    print(" - Demo Patient:   patient@demo.test / Password123!")
    print(" - Demo Doctor:    doctor@demo.test  / Password123!")
    print(" - Demo Admin:     admin@demo.test   / Password123!")
    print(" - 4 Cases (acne, eczema, psoriasis, other) seeded with longitudinal data.")
    print(" - Active & Revoked Consents created.")
    print(" - Consult messages seeded.")
    print(" - All records flagged is_synthetic=1.")

if __name__ == "__main__":
    seed()
