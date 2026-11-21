"""
clinics.py router — Nearby and search endpoints.
"""
from app.services.clinics import search_nearby_clinics, search_clinics_by_text, purchase_partner_package
from app.core.db import get_db
from app.errors import NotFoundException

def get_nearby_clinics_endpoint(lat: float, lng: float, radius_km: float = 10.0, limit: int = 20, user_id: str = "guest", ip: str = "127.0.0.1") -> list:
    return search_nearby_clinics(lat, lng, radius_km, limit, user_id, ip)

def search_clinics_endpoint(district: str = None, city: str = None, limit: int = 20) -> list:
    return search_clinics_by_text(district, city, limit)

def get_clinic_detail_endpoint(clinic_id: str) -> dict:
    db = get_db()
    c = db.execute("SELECT * FROM clinics WHERE id = ?", (clinic_id,)).fetchone()
    if not c:
        raise NotFoundException("Phòng khám không tồn tại")
    return dict(c)
