"""
logging.py — Structured JSON logger with privacy scrubbing.
Rules:
- Scrub raw images, symptom text, consult messages, exact GPS coordinates (round to 2 decimals).
- Output standard JSON with timestamp, request_id, level, message.
"""
import json
import re
import datetime
import sys

def scrub_data(obj):
    """Recursively scrub sensitive PII and health information from logs."""
    if isinstance(obj, dict):
        scrubbed = {}
        for k, v in obj.items():
            k_lower = k.lower()
            if any(term in k_lower for term in ["image", "bytes", "content", "token", "password", "secret", "body", "symptom", "note", "message"]):
                scrubbed[k] = "[SCRUBBED]"
            elif k_lower in ["lat", "lng", "latitude", "longitude"]:
                try:
                    scrubbed[k] = round(float(v), 2)
                except Exception:
                    scrubbed[k] = "[SCRUBBED_COORD]"
            elif k_lower == "email":
                if isinstance(v, str) and "@" in v:
                    parts = v.split("@")
                    scrubbed[k] = f"{parts[0][:2]}***@{parts[1]}"
                else:
                    scrubbed[k] = "[SCRUBBED_EMAIL]"
            else:
                scrubbed[k] = scrub_data(v)
        return scrubbed
    elif isinstance(obj, list):
        return [scrub_data(item) for item in obj]
    elif isinstance(obj, str):
        # Scrub email pattern
        s = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_SCRUBBED]', obj)
        return s
    return obj

def log(level: str, message: str, request_id: str = "sys", extra: dict = None):
    """Write structured JSON log line."""
    payload = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "level": level.upper(),
        "req_id": request_id,
        "msg": scrub_data(message),
    }
    if extra:
        payload["data"] = scrub_data(extra)
    print(json.dumps(payload, ensure_ascii=False), file=sys.stdout, flush=True)

def info(message: str, request_id: str = "sys", extra: dict = None):
    log("INFO", message, request_id, extra)

def warn(message: str, request_id: str = "sys", extra: dict = None):
    log("WARN", message, request_id, extra)

def error(message: str, request_id: str = "sys", extra: dict = None):
    log("ERROR", message, request_id, extra)
