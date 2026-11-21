"""
db.py — Database management and SQLite / PostgreSQL engine.
Supports all 26+ tables specified in Section 6 of MASTER_SPEC.md.
Includes cosine similarity vector search in pure Python/SQLite for standalone operation,
and ready for PostgreSQL pgvector.
"""
import os
import sqlite3
import json
import math
import datetime

import threading

DB_PATH = "data/derma.db"

_local = threading.local()

def get_db():
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        _local.conn = conn
    return _local.conn

def close_db():
    if hasattr(_local, "conn") and _local.conn is not None:
        try:
            _local.conn.close()
        except Exception:
            pass
        _local.conn = None

def cosine_similarity(v1: list, v2: list) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a, b in zip(v1, v1)))
    norm2 = math.sqrt(sum(b * b for a, b in zip(v2, v2)))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def init_db():
    """Create all required tables with UUID primary keys and timestamps."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        display_name TEXT,
        role TEXT NOT NULL CHECK(role IN ('patient', 'clinician', 'admin')),
        auth_provider TEXT NOT NULL CHECK(auth_provider IN ('local', 'privy')),
        auth_subject TEXT UNIQUE,
        password_hash TEXT,
        locale TEXT DEFAULT 'vi',
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'disabled')),
        privacy_accepted_at TEXT,
        privacy_version TEXT,
        terms_version TEXT,
        terms_accepted_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 2. clinics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinics (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE,
        name TEXT NOT NULL,
        address_text TEXT NOT NULL,
        address_note TEXT,
        city TEXT DEFAULT 'TP. Hồ Chí Minh',
        district TEXT,
        lat REAL,
        lng REAL,
        geocode_status TEXT DEFAULT 'pending' CHECK(geocode_status IN ('pending', 'ok', 'failed', 'manual')),
        phone TEXT,
        hours_note TEXT,
        listing_type TEXT NOT NULL CHECK(listing_type IN ('directory', 'partner_candidate', 'partner')),
        source_url TEXT,
        source_checked_at TEXT,
        status TEXT DEFAULT 'active',
        verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
        partner_until TEXT,
        is_synthetic INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 3. clinician_profiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinician_profiles (
        user_id TEXT PRIMARY KEY,
        clinic_id TEXT NOT NULL,
        clinic_role TEXT NOT NULL CHECK(clinic_role IN ('owner', 'doctor')),
        license_no_enc TEXT,
        verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'rejected')),
        verified_by TEXT,
        verified_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(clinic_id) REFERENCES clinics(id)
    );
    """)

    # 4. partner_subscriptions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partner_subscriptions (
        id TEXT PRIMARY KEY,
        clinic_id TEXT NOT NULL,
        tier TEXT DEFAULT 'verified_partner',
        starts_at TEXT NOT NULL,
        ends_at TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending', 'active', 'expired', 'failed')),
        settlement_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(clinic_id) REFERENCES clinics(id)
    );
    """)

    # 5. wallets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        id TEXT PRIMARY KEY,
        user_id TEXT UNIQUE NOT NULL,
        address TEXT NOT NULL,
        provider TEXT DEFAULT 'local-dev' CHECK(provider IN ('privy', 'local-dev')),
        terms_accepted_at TEXT,
        enc_key_ref TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    # 6. cases
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        profile_type TEXT NOT NULL CHECK(profile_type IN ('acne', 'eczema', 'psoriasis', 'other')),
        diagnosis_status TEXT DEFAULT 'unknown' CHECK(diagnosis_status IN ('clinician_diagnosed', 'unknown')),
        title TEXT,
        body_site TEXT NOT NULL,
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused', 'closed')),
        cadence_days INTEGER DEFAULT 7,
        clinician_id TEXT,
        is_synthetic INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(patient_id) REFERENCES users(id)
    );
    """)

    # 7. observations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS observations (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        captured_at TEXT NOT NULL,
        workflow_state TEXT NOT NULL,
        quality_status TEXT CHECK(quality_status IN ('PASS', 'RETAKE', 'REVIEW')),
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id)
    );
    """)

    # 8. image_assets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS image_assets (
        id TEXT PRIMARY KEY,
        observation_id TEXT NOT NULL,
        view_type TEXT NOT NULL CHECK(view_type IN ('overview', 'closeup')),
        object_key TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        phash TEXT NOT NULL,
        mime TEXT NOT NULL,
        width INTEGER NOT NULL,
        height INTEGER NOT NULL,
        dek_wrapped TEXT NOT NULL,
        exif_stripped INTEGER DEFAULT 1,
        consent_scope_ref TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(observation_id) REFERENCES observations(id)
    );
    """)

    # 9. roi_annotations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roi_annotations (
        id TEXT PRIMARY KEY,
        observation_id TEXT NOT NULL,
        image_id TEXT NOT NULL,
        method TEXT NOT NULL CHECK(method IN ('user_drawn', 'face_landmarks', 'auto')),
        geometry TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(observation_id) REFERENCES observations(id),
        FOREIGN KEY(image_id) REFERENCES image_assets(id)
    );
    """)

    # 10. quality_reports
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quality_reports (
        id TEXT PRIMARY KEY,
        image_id TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('PASS', 'RETAKE', 'REVIEW')),
        metrics TEXT NOT NULL,
        reasons TEXT NOT NULL,
        thresholds_version TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(image_id) REFERENCES image_assets(id)
    );
    """)

    # 11. visual_measurements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visual_measurements (
        id TEXT PRIMARY KEY,
        observation_id TEXT NOT NULL,
        metric_name TEXT NOT NULL,
        value REAL NOT NULL,
        unit TEXT,
        confidence REAL NOT NULL,
        model_version TEXT NOT NULL,
        provenance TEXT NOT NULL CHECK(provenance IN ('ai_measured', 'user_reported', 'clinician_entered', 'synthetic')),
        roi_id TEXT,
        details TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(observation_id) REFERENCES observations(id)
    );
    """)

    # 12. knowledge_conditions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_conditions (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE NOT NULL,
        name_vi TEXT NOT NULL,
        name_en TEXT NOT NULL,
        summary_vi TEXT NOT NULL,
        summary_en TEXT NOT NULL,
        typical_features TEXT NOT NULL,
        body_sites TEXT NOT NULL,
        embedding TEXT NOT NULL,
        sources TEXT NOT NULL,
        reviewed_by_clinician INTEGER DEFAULT 0,
        reviewed_by TEXT,
        reviewed_at TEXT,
        version TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 13. similar_condition_results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS similar_condition_results (
        id TEXT PRIMARY KEY,
        observation_id TEXT NOT NULL,
        symptom_entry_id TEXT,
        embedder_version TEXT NOT NULL,
        kb_version TEXT NOT NULL,
        results TEXT NOT NULL,
        abstain_reason TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(observation_id) REFERENCES observations(id)
    );
    """)

    # 14. comparisons
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comparisons (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        obs_from TEXT NOT NULL,
        obs_to TEXT NOT NULL,
        flag TEXT NOT NULL CHECK(flag IN ('COMPARABLE', 'PARTIAL', 'NOT_COMPARABLE')),
        reasons TEXT NOT NULL,
        deltas TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id)
    );
    """)

    # 15. symptom_entries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symptom_entries (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        entered_at TEXT NOT NULL,
        form_version TEXT NOT NULL,
        answers TEXT NOT NULL,
        recall_window_days INTEGER DEFAULT 7,
        provenance TEXT DEFAULT 'user_reported',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id)
    );
    """)

    # 16. clinician_reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinician_reviews (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        clinician_id TEXT NOT NULL,
        note TEXT,
        clinician_scores TEXT,
        plan TEXT,
        next_followup_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id),
        FOREIGN KEY(clinician_id) REFERENCES users(id)
    );
    """)

    # 17. consents
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consents (
        id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        case_id TEXT NOT NULL,
        recipient_clinic_id TEXT NOT NULL,
        recipient_user_id TEXT,
        scope TEXT NOT NULL,
        purpose TEXT,
        expires_at TEXT NOT NULL,
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'revoked', 'expired')),
        revoked_at TEXT,
        commitment TEXT NOT NULL,
        nonce_enc TEXT NOT NULL,
        grant_tx_id TEXT,
        revoke_tx_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(patient_id) REFERENCES users(id),
        FOREIGN KEY(case_id) REFERENCES cases(id),
        FOREIGN KEY(recipient_clinic_id) REFERENCES clinics(id)
    );
    """)

    # 18. consult_messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consult_messages (
        id TEXT PRIMARY KEY,
        consent_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        body TEXT NOT NULL,
        sent_at TEXT NOT NULL,
        read_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(consent_id) REFERENCES consents(id),
        FOREIGN KEY(sender_id) REFERENCES users(id)
    );
    """)

    # 19. access_requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS access_requests (
        id TEXT PRIMARY KEY,
        clinician_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        case_id TEXT,
        message TEXT,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'denied')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(clinician_id) REFERENCES users(id),
        FOREIGN KEY(patient_id) REFERENCES users(id)
    );
    """)

    # 20. appointments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        clinician_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        scheduled_at TEXT NOT NULL,
        status TEXT DEFAULT 'proposed' CHECK(status IN ('proposed', 'confirmed', 'cancelled', 'done')),
        note TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id),
        FOREIGN KEY(clinician_id) REFERENCES users(id),
        FOREIGN KEY(patient_id) REFERENCES users(id)
    );
    """)

    # 21. reminders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        kind TEXT NOT NULL CHECK(kind IN ('capture', 'symptom', 'followup')),
        due_at TEXT NOT NULL,
        status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'sent', 'done', 'cancelled')),
        channel TEXT DEFAULT 'in_app' CHECK(channel IN ('in_app', 'email')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    # 22. notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        type TEXT NOT NULL,
        payload TEXT NOT NULL,
        read_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    # 23. reports
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        version TEXT NOT NULL,
        audience TEXT NOT NULL CHECK(audience IN ('patient', 'clinician')),
        content TEXT NOT NULL,
        pdf_object_key TEXT,
        generated_by TEXT DEFAULT 'template' CHECK(generated_by IN ('template', 'llm')),
        source_refs TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id)
    );
    """)

    # 24. agent_runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_runs (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        observation_id TEXT,
        state_history TEXT,
        tool_calls TEXT,
        rule_hits TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(case_id) REFERENCES cases(id)
    );
    """)

    # 25. audit_events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        result TEXT NOT NULL CHECK(result IN ('allow', 'deny', 'error')),
        ip_hash TEXT NOT NULL,
        ts TEXT NOT NULL,
        anchor_batch_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 26. audit_anchor_batches
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_anchor_batches (
        id TEXT PRIMARY KEY,
        merkle_root TEXT NOT NULL,
        event_count INTEGER NOT NULL,
        chain_tx_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 27. chain_transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chain_transactions (
        id TEXT PRIMARY KEY,
        kind TEXT NOT NULL CHECK(kind IN ('consent_grant', 'consent_revoke', 'audit_anchor', 'settlement')),
        idempotency_key TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('CREATED', 'SIGNED', 'SUBMITTED', 'CONFIRMED', 'FAILED', 'TIMEOUT')),
        tx_hash TEXT,
        chain_id INTEGER NOT NULL,
        error TEXT,
        attempts INTEGER DEFAULT 0,
        block_number INTEGER,
        confirmed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 28. settlements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settlements (
        id TEXT PRIMARY KEY,
        invoice_ref TEXT UNIQUE NOT NULL,
        invoice_type TEXT NOT NULL CHECK(invoice_type IN ('partner_package', 'demo')),
        patient_id TEXT,
        clinic_id TEXT,
        amount_test REAL NOT NULL,
        status TEXT NOT NULL,
        chain_tx_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 29. model_registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_registry (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        version TEXT NOT NULL,
        metrics TEXT,
        card_path TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_patient ON cases(patient_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_obs_case_date ON observations(case_id, captured_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clinics_lat_lng ON clinics(lat, lng);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_consents_clinic ON consents(recipient_clinic_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_id);")

    conn.commit()
