"""
audit.py — Audit trail logger for DermaCare Agent.
Tracks all access to health data (allow / deny / error).
Zero PII in audit records.
"""
import uuid
import datetime
import hashlib
import json
from app.core.db import get_db

IP_SALT = "dermacare_ip_salt_2026"

def hash_ip(ip_address: str) -> str:
    """Anonymize IP address with SHA256 and salt."""
    if not ip_address:
        return "unknown"
    return hashlib.sha256(f"{ip_address}:{IP_SALT}".encode('utf-8')).hexdigest()[:16]

def record_audit_event(
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    result: str = "allow",  # allow | deny | error
    ip_address: str = "127.0.0.1",
    details: dict = None
) -> str:
    """Record an audit event to the audit_events table."""
    event_id = str(uuid.uuid4())
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ip_h = hash_ip(ip_address)
    now = ts

    db = get_db()
    db.execute(
        """
        INSERT INTO audit_events (id, actor_id, actor_role, action, resource_type, resource_id, result, ip_hash, ts, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, actor_id or "anonymous", actor_role or "guest", action, resource_type, resource_id, result, ip_h, ts, now, now)
    )
    db.commit()
    return event_id
