"""
reminders.py — Router for Reminders and Notifications.
"""
from app.core.db import get_db
from app.core.audit import record_audit_event
import uuid
import datetime
import json

def schedule_reminder(user_id: str, case_id: str, kind: str = "capture", due_days: int = 7, ip: str = "127.0.0.1") -> dict:
    rem_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc)
    due_at = (now + datetime.timedelta(days=due_days)).isoformat()
    now_iso = now.isoformat()

    db = get_db()
    db.execute(
        """
        INSERT INTO reminders (id, case_id, user_id, kind, due_at, status, channel, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'scheduled', 'in_app', ?, ?)
        """,
        (rem_id, case_id, user_id, kind, due_at, now_iso, now_iso)
    )

    # In-app notification
    notif_id = str(uuid.uuid4())
    payload = json.dumps({
        "case_id": case_id,
        "message": f"Nhắc lịch chụp ảnh theo dõi đúng khung chuẩn ({kind})"
    })
    db.execute(
        """
        INSERT INTO notifications (id, user_id, type, payload, created_at, updated_at)
        VALUES (?, ?, 'reminder_due', ?, ?, ?)
        """,
        (notif_id, user_id, payload, now_iso, now_iso)
    )
    db.commit()

    record_audit_event(user_id, "patient", "schedule_reminder", "reminder", rem_id, "allow", ip)
    return {"id": rem_id, "due_at": due_at, "status": "scheduled"}

def list_user_notifications(user_id: str, ip: str = "127.0.0.1") -> list:
    db = get_db()
    rows = db.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"]) if isinstance(d["payload"], str) else d["payload"]
        res.append(d)
    record_audit_event(user_id, "user", "list_notifications", "notification", "all", "allow", ip)
    return res
