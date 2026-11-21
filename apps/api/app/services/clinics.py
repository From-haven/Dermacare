"""
clinics.py — Clinic Management, GPS Haversine Distance, and Partner Subscription.
Rules (Section 11 Master Spec):
- Haversine distance from user lat/lng.
- Order: (1) Verified Partner (partner_until > now) FIRST, (2) then distance ASC.
- Verified Partner has "Đối tác xác thực — hiển thị ưu tiên theo gói đối tác" and button "Gửi hồ sơ & Tư vấn ngay".
- Directory clinics: public directory only, NO partner label, NO consent button.
- User GPS is NEVER stored in database. Log rounded to 2 decimals.
"""
import math
import os
import yaml
import uuid
import datetime
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.errors import LocationInvalidException, ValidationException, NotFoundException, ForbiddenException
from app.config import CLINIC_SEARCH_MAX_RADIUS_KM, CLINIC_SEARCH_DEFAULT_RADIUS_KM

DIRECTORY_YAML = "apps/api/app/data/clinics_directory.yaml"
DEMO_YAML = "apps/api/app/data/clinics_demo.yaml"

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth in km."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def sync_clinics():
    """Load both directory (real) and demo (synthetic) clinics into database."""
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Real clinics (directory)
    if os.path.exists(DIRECTORY_YAML):
        with open(DIRECTORY_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for c in data.get("clinics", []):
            slug = c["slug"]
            existing = db.execute("SELECT id FROM clinics WHERE slug = ?", (slug,)).fetchone()
            if not existing:
                cid = str(uuid.uuid4())
                source_url = c.get("sources", [{}])[0].get("url")
                db.execute(
                    """
                    INSERT INTO clinics (
                        id, slug, name, address_text, address_note, city, district,
                        lat, lng, geocode_status, phone, hours_note, listing_type,
                        source_url, source_checked_at, status, verification_status,
                        partner_until, is_synthetic, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'directory', ?, ?, 'active', 'verified', NULL, 0, ?, ?)
                    """,
                    (cid, slug, c["name"], c["address_text"], c.get("address_note"),
                     data.get("city", "TP. Hồ Chí Minh"), c.get("district"),
                     c.get("lat"), c.get("lng"), c.get("geocode_status", "ok"),
                     c.get("phone"), c.get("hours_note"), source_url, data.get("checked_at"), now, now)
                )

    # 2. Demo clinics (synthetic)
    if os.path.exists(DEMO_YAML):
        with open(DEMO_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for c in data.get("clinics", []):
            slug = c["slug"]
            existing = db.execute("SELECT id FROM clinics WHERE slug = ?", (slug,)).fetchone()
            if not existing:
                cid = str(uuid.uuid4())
                partner_until = None
                if c.get("partner_active"):
                    days = c.get("partner_days", 30)
                    partner_until = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)).isoformat()

                db.execute(
                    """
                    INSERT INTO clinics (
                        id, slug, name, address_text, address_note, city, district,
                        lat, lng, geocode_status, phone, hours_note, listing_type,
                        status, verification_status, partner_until, is_synthetic, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ok', ?, ?, ?, 'active', ?, ?, 1, ?, ?)
                    """,
                    (cid, slug, c["name"], c["address_text"], c.get("address_note"),
                     data.get("city", "TP. Hồ Chí Minh"), c.get("district"),
                     c.get("lat"), c.get("lng"), c.get("phone"), c.get("hours_note"),
                     c.get("listing_type", "partner"), c.get("verification_status", "verified"),
                     partner_until, now, now)
                )
    db.commit()

def search_nearby_clinics(
    lat: float,
    lng: float,
    radius_km: float = CLINIC_SEARCH_DEFAULT_RADIUS_KM,
    limit: int = 20,
    user_id: str = "guest",
    ip: str = "127.0.0.1"
) -> list:
    """
    Search clinics near coordinates using haversine formula.
    Sorting:
      1. Verified Partner (partner_until > now) FIRST.
      2. Distance in km ascending.
    """
    sync_clinics()

    if lat < -90 or lat > 90 or lng < -180 or lng > 180:
        raise LocationInvalidException("Toạ độ GPS không hợp lệ (lat: [-90, 90], lng: [-180, 180])")

    radius_km = min(float(radius_km), CLINIC_SEARCH_MAX_RADIUS_KM)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM clinics
        WHERE verification_status = 'verified' AND lat IS NOT NULL AND lng IS NOT NULL
        """
    ).fetchall()

    results = []
    for r in rows:
        d_km = haversine_distance_km(lat, lng, r["lat"], r["lng"])
        if d_km <= radius_km:
            is_partner = bool(r["partner_until"] and r["partner_until"] > now_iso and r["listing_type"] == "partner")
            item = {
                "id": r["id"],
                "name": r["name"],
                "address_text": r["address_text"],
                "address_note": r["address_note"],
                "district": r["district"],
                "phone": r["phone"],
                "hours_note": r["hours_note"],
                "lat": r["lat"],
                "lng": r["lng"],
                "distance_km": d_km,
                "listing_type": r["listing_type"],
                "is_partner": is_partner,
                "is_synthetic": bool(r["is_synthetic"])
            }

            if is_partner:
                item["partner_label"] = "Đối tác xác thực — hiển thị ưu tiên theo gói đối tác"
                item["can_send_consent"] = True
            else:
                item["partner_label"] = None
                item["can_send_consent"] = False
                if r["listing_type"] == "directory":
                    item["public_note"] = "Thông tin công khai, vui lòng gọi điện xác nhận trước khi đến khám"

            results.append(item)

    # SORTING: (1) Partner first (is_partner=True first), (2) distance ascending
    results.sort(key=lambda x: (0 if x["is_partner"] else 1, x["distance_km"]))

    # Audit logging: record rounded coordinates only (zero exact GPS in log)
    record_audit_event(user_id, "user", "search_nearby_clinics", "clinic", f"{round(lat, 2)},{round(lng, 2)}", "allow", ip)

    return results[:limit]

def search_clinics_by_text(district: str = None, city: str = None, limit: int = 20) -> list:
    """Manual fallback search when user denies GPS access."""
    sync_clinics()
    db = get_db()
    query = "SELECT * FROM clinics WHERE verification_status = 'verified'"
    params = []

    if district:
        query += " AND district LIKE ?"
        params.append(f"%{district}%")
    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")

    query += " ORDER BY CASE WHEN partner_until IS NOT NULL THEN 0 ELSE 1 END, name ASC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, tuple(params)).fetchall()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    res = []
    for r in rows:
        is_partner = bool(r["partner_until"] and r["partner_until"] > now_iso and r["listing_type"] == "partner")
        res.append({
            "id": r["id"],
            "name": r["name"],
            "address_text": r["address_text"],
            "district": r["district"],
            "phone": r["phone"],
            "lat": r["lat"],
            "lng": r["lng"],
            "is_partner": is_partner,
            "can_send_consent": is_partner,
            "is_synthetic": bool(r["is_synthetic"])
        })
    return res

def purchase_partner_package(clinic_id: str, clinician_id: str, simulate_tx_status: str = "CONFIRMED", ip: str = "127.0.0.1") -> dict:
    """
    Purchase Verified Partner package using test tokens.
    Requires clinic to be verified and clinician to be verified owner.
    """
    db = get_db()
    # Check clinic
    clinic = db.execute("SELECT * FROM clinics WHERE id = ?", (clinic_id,)).fetchone()
    if not clinic:
        raise NotFoundException("Phòng khám không tồn tại")
    if clinic["verification_status"] != "verified":
        raise ForbiddenException("Phòng khám chưa được admin duyệt")

    # Check clinician is owner
    prof = db.execute("SELECT * FROM clinician_profiles WHERE user_id = ? AND clinic_id = ?", (clinician_id, clinic_id)).fetchone()
    if not prof or prof["verification_status"] != "verified" or prof["clinic_role"] != "owner":
        raise ForbiddenException("Chỉ chủ phòng khám (owner) đã được duyệt mới có quyền mua gói Partner")

    sub_id = str(uuid.uuid4())
    settlement_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.isoformat()
    ends_at = (now + datetime.timedelta(days=30)).isoformat()

    # Create settlement record
    db.execute(
        """
        INSERT INTO settlements (id, invoice_ref, invoice_type, clinic_id, amount_test, status, created_at, updated_at)
        VALUES (?, ?, 'partner_package', ?, 100.0, ?, ?, ?)
        """,
        (settlement_id, f"0x{uuid.uuid4().hex}", clinic_id, simulate_tx_status, now_iso, now_iso)
    )

    if simulate_tx_status == "CONFIRMED":
        # T10: Only activate Partner if CONFIRMED!
        sub_status = "active"
        db.execute(
            "UPDATE clinics SET partner_until = ?, listing_type = 'partner', updated_at = ? WHERE id = ?",
            (ends_at, now_iso, clinic_id)
        )
    else:
        # FAILED or TIMEOUT -> do NOT activate partner!
        sub_status = "failed"

    db.execute(
        """
        INSERT INTO partner_subscriptions (id, clinic_id, tier, starts_at, ends_at, status, settlement_id, created_at, updated_at)
        VALUES (?, ?, 'verified_partner', ?, ?, ?, ?, ?, ?)
        """,
        (sub_id, clinic_id, now_iso, ends_at, sub_status, settlement_id, now_iso, now_iso)
    )
    db.commit()

    record_audit_event(clinician_id, "clinician", "purchase_partner", "clinic", clinic_id, "allow", ip)

    return {
        "subscription_id": sub_id,
        "status": sub_status,
        "partner_until": ends_at if sub_status == "active" else None,
        "transaction_status": simulate_tx_status
    }
