"""
main.py — DermaCare Agent Unified HTTP API & Web Dispatcher Server.
Serves:
- REST API under /api/... and /health
- Web Application & Static Assets from apps/web/
- In-memory Rate Limiting according to Section 7 (5/min login, 20/hr upload, 30/min clinic search)
- Full REST CRUD methods (GET, POST, PUT, PATCH, DELETE, OPTIONS)
"""
import sys
import os
import re
import json
import time
import base64
import uuid
import datetime
from collections import defaultdict
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Add workspace and apps/api to path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "apps/api"))
sys.path.insert(0, WORKSPACE_ROOT)

from app.config import settings
from app.errors import (
    DermaCareException, UnauthenticatedException, ForbiddenException,
    NotFoundException, ValidationException, RateLimitedException
)
from app.core.security import decode_access_token
from app.core.db import get_db
from app.core.rbac import enforce_admin, check_patient_owns_case
from app.core.audit import record_audit_event
from app.agent.safety import evaluate_safety_rules
from app.agent.graph import run_agent_workflow
from app.services.timeline import generate_timeline
from app.services.pdf_export import generate_pdf_report
from ml.vision.compare import evaluate_comparability

# Import routers
from app.routers import (
    auth, cases, images, reports, clinics, consents,
    consults, clinician, admin, chain, reminders
)

# Rate limiting store (key, action) -> list of timestamps
RATE_LIMITS = {
    "login": (5, 60),          # 5 requests per minute
    "upload": (20, 3600),      # 20 requests per hour
    "clinic_search": (30, 60), # 30 requests per minute
}
_rate_store = defaultdict(list)

def check_rate_limit(key: str, action: str):
    limit, window = RATE_LIMITS.get(action, (1000, 60))
    now = time.time()
    timestamps = [t for t in _rate_store[(key, action)] if now - t < window]
    if len(timestamps) >= limit:
        _rate_store[(key, action)] = timestamps
        raise RateLimitedException(f"Vượt quá giới hạn {limit} yêu cầu trong {window}s. Vui lòng thử lại sau.")
    timestamps.append(now)
    _rate_store[(key, action)] = timestamps

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class DermaCareHandler(BaseHTTPRequestHandler):
    def get_client_ip(self) -> str:
        fwd = self.headers.get("X-Forwarded-For")
        if fwd:
            return fwd.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "127.0.0.1"

    def send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()
        self.wfile.write(body)

    def send_binary(self, status: int, data: bytes, content_type: str, filename: str = None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()
        self.wfile.write(data)

    def send_file_response(self, file_path: str, content_type: str):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "File not found", "details": {}}})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()

    def get_auth_token(self) -> str:
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        return None

    def get_authenticated_user_id(self) -> str:
        token = self.get_auth_token()
        if not token:
            raise UnauthenticatedException("Yêu cầu xác thực tài khoản")
        payload = decode_access_token(token)
        return payload["sub"]

    def parse_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw_data = self.rfile.read(content_length)
            try:
                return json.loads(raw_data.decode("utf-8"))
            except Exception:
                return {"_raw": raw_data}
        return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Health
        if path == "/health":
            return self.send_json(200, {
                "status": "ok",
                "app": "DermaCare Agent",
                "version": "1.0.0",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

        # Static assets
        if path.startswith("/static/"):
            rel_path = path[8:]
            full_path = os.path.join(WORKSPACE_ROOT, "apps/web", rel_path)
            ext = os.path.splitext(rel_path)[1].lower()
            ct = "text/plain"
            if ext == ".css": ct = "text/css"
            elif ext == ".js": ct = "application/javascript"
            elif ext in [".svg"]: ct = "image/svg+xml"
            elif ext in [".png"]: ct = "image/png"
            elif ext in [".jpg", ".jpeg"]: ct = "image/jpeg"
            return self.send_file_response(full_path, ct)

        # API Routes
        if path.startswith("/api/"):
            try:
                return self.dispatch_api_get(path, query)
            except DermaCareException as de:
                return self.send_json(de.status_code, de.to_dict())
            except Exception as e:
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e), "details": {}}})

        # Web SPA Fallback: serve apps/web/index.html
        index_file = os.path.join(WORKSPACE_ROOT, "apps/web/index.html")
        return self.send_file_response(index_file, "text/html; charset=utf-8")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                body = self.parse_body()
                return self.dispatch_api_post(path, body)
            except DermaCareException as de:
                return self.send_json(de.status_code, de.to_dict())
            except Exception as e:
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e), "details": {}}})

        self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "Endpoint not found", "details": {}}})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                body = self.parse_body()
                return self.dispatch_api_put(path, body)
            except DermaCareException as de:
                return self.send_json(de.status_code, de.to_dict())
            except Exception as e:
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e), "details": {}}})

        self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "Endpoint not found", "details": {}}})

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                body = self.parse_body()
                return self.dispatch_api_patch(path, body)
            except DermaCareException as de:
                return self.send_json(de.status_code, de.to_dict())
            except Exception as e:
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e), "details": {}}})

        self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "Endpoint not found", "details": {}}})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            try:
                return self.dispatch_api_delete(path)
            except DermaCareException as de:
                return self.send_json(de.status_code, de.to_dict())
            except Exception as e:
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e), "details": {}}})

        self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "Endpoint not found", "details": {}}})

    # -------------------------------------------------------------
    # GET DISPATCHER
    # -------------------------------------------------------------
    def dispatch_api_get(self, path: str, query: dict):
        ip = self.get_client_ip()

        # /api/me
        if path == "/api/me":
            token = self.get_auth_token()
            if not token:
                raise UnauthenticatedException("Chưa đăng nhập")
            return self.send_json(200, auth.get_current_user(token))

        if path == "/api/me/export":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, auth.export_my_data(uid))

        # /api/profiles
        if path == "/api/profiles":
            return self.send_json(200, cases.list_profiles())

        match_prof = re.match(r"^/api/profiles/([a-zA-Z0-9_\-]+)$", path)
        if match_prof:
            return self.send_json(200, cases.get_profile(match_prof.group(1)))

        # /api/cases
        if path == "/api/cases":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.list_user_cases(uid))

        match_case_tl = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/timeline$", path)
        if match_case_tl:
            uid = self.get_authenticated_user_id()
            case_id = match_case_tl.group(1)
            check_patient_owns_case(uid, case_id, ip)
            metric = query.get("metric", ["affected_area_ratio"])[0]
            db = get_db()
            case_row = db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
            # Fetch observations
            obs_rows = db.execute(
                """
                SELECT o.id, o.captured_at, vm.metric_name, vm.value, c.flag as comp_flag
                FROM observations o
                LEFT JOIN visual_measurements vm ON o.id = vm.observation_id AND vm.metric_name = ?
                LEFT JOIN comparisons c ON o.id = c.obs_b_id
                WHERE o.case_id = ?
                ORDER BY o.captured_at ASC
                """,
                (metric, case_id)
            ).fetchall()
            obs_list = []
            for r in obs_rows:
                obs_list.append({
                    "id": r["id"],
                    "captured_at": r["captured_at"],
                    "comparison_flag": r["comp_flag"] or "COMPARABLE",
                    "measurements": {metric: r["value"] if r["value"] is not None else 0.0}
                })
            tl = generate_timeline(obs_list, profile_type=case_row["profile_type"] if case_row else "other", metric_name=metric)
            return self.send_json(200, tl)

        match_case_reps = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/reports$", path)
        if match_case_reps:
            uid = self.get_authenticated_user_id()
            case_id = match_case_reps.group(1)
            check_patient_owns_case(uid, case_id, ip)
            db = get_db()
            rows = db.execute("SELECT id, case_id, version, audience, created_at FROM reports WHERE case_id = ? ORDER BY created_at DESC", (case_id,)).fetchall()
            return self.send_json(200, [dict(r) for r in rows])

        match_case = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)$", path)
        if match_case:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.get_case(uid, match_case.group(1)))

        match_sym = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/symptoms$", path)
        if match_sym:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.get_case_symptoms(uid, match_sym.group(1)))

        # /api/reports/<id>/pdf
        match_rep_pdf = re.match(r"^/api/reports/([a-zA-Z0-9_\-]+)/pdf$", path)
        if match_rep_pdf:
            uid = self.get_authenticated_user_id()
            rep = reports.get_report(match_rep_pdf.group(1), uid, ip)
            pdf_bytes = generate_pdf_report(rep["content"])
            return self.send_binary(200, pdf_bytes, "application/pdf", filename=f"report_{match_rep_pdf.group(1)[:8]}.pdf")

        # /api/reports/<id>
        match_rep = re.match(r"^/api/reports/([a-zA-Z0-9_\-]+)$", path)
        if match_rep:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, reports.get_report(match_rep.group(1), uid, ip))

        # /api/images/<id>/content?token=...
        match_img_content = re.match(r"^/api/images/([a-zA-Z0-9_\-]+)/content$", path)
        if match_img_content:
            token = query.get("token", [None])[0]
            if not token:
                raise UnauthenticatedException("Thiếu token xem ảnh")
            clean_bytes, mime = images.get_image_content(match_img_content.group(1), token, ip)
            return self.send_binary(200, clean_bytes, mime)

        # /api/images/<id>/meta
        match_img_meta = re.match(r"^/api/images/([a-zA-Z0-9_\-]+)/meta$", path)
        if match_img_meta:
            db = get_db()
            img = db.execute("SELECT id, observation_id, view_type, width, height, mime, quality_status, created_at FROM image_assets WHERE id = ?", (match_img_meta.group(1),)).fetchone()
            if not img:
                raise NotFoundException("Ảnh không tồn tại")
            return self.send_json(200, dict(img))

        # /api/images/<id>/quality
        match_img_q = re.match(r"^/api/images/([a-zA-Z0-9_\-]+)/quality$", path)
        if match_img_q:
            db = get_db()
            q = db.execute("SELECT * FROM quality_metrics WHERE image_asset_id = ? ORDER BY created_at DESC LIMIT 1", (match_img_q.group(1),)).fetchone()
            if not q:
                raise NotFoundException("Chưa có đánh giá chất lượng cho ảnh này")
            return self.send_json(200, dict(q))

        # /api/observations/<id>/analysis
        match_obs_an = re.match(r"^/api/observations/([a-zA-Z0-9_\-]+)/analysis$", path)
        if match_obs_an:
            obs_id = match_obs_an.group(1)
            db = get_db()
            measures = db.execute("SELECT * FROM visual_measurements WHERE observation_id = ?", (obs_id,)).fetchall()
            return self.send_json(200, {"observation_id": obs_id, "measurements": [dict(m) for m in measures]})

        # /api/observations/<id>/similar-conditions
        match_obs_sim = re.match(r"^/api/observations/([a-zA-Z0-9_\-]+)/similar-conditions$", path)
        if match_obs_sim:
            obs_id = match_obs_sim.group(1)
            db = get_db()
            sims = db.execute("SELECT * FROM similar_condition_results WHERE observation_id = ?", (obs_id,)).fetchall()
            return self.send_json(200, {
                "observation_id": obs_id,
                "disclaimer": "Các tình trạng có biểu hiện tương đồng (chỉ để tham khảo). Đây không phải chẩn đoán.",
                "items": [dict(s) for s in sims]
            })

        # /api/clinics/nearby
        if path == "/api/clinics/nearby":
            check_rate_limit(ip, "clinic_search")
            lat = float(query.get("lat", [10.7769])[0])
            lng = float(query.get("lng", [106.7009])[0])
            radius = float(query.get("radius_km", [10.0])[0])
            uid = "guest"
            try: uid = self.get_authenticated_user_id()
            except Exception: pass
            return self.send_json(200, clinics.get_nearby_clinics_endpoint(lat, lng, radius, user_id=uid))

        # /api/clinics/search
        if path == "/api/clinics/search":
            check_rate_limit(ip, "clinic_search")
            district = query.get("district", [None])[0]
            city = query.get("city", [None])[0]
            return self.send_json(200, clinics.search_clinics_endpoint(district=district, city=city))

        # /api/clinics/<id>
        match_clinic = re.match(r"^/api/clinics/([a-zA-Z0-9_\-]+)$", path)
        if match_clinic:
            return self.send_json(200, clinics.get_clinic_detail_endpoint(match_clinic.group(1)))

        # /api/clinic/partner
        if path == "/api/clinic/partner":
            uid = self.get_authenticated_user_id()
            db = get_db()
            prof = db.execute("SELECT * FROM clinician_profiles WHERE user_id = ?", (uid,)).fetchone()
            if not prof:
                raise ForbiddenException("Bạn chưa tạo hồ sơ bác sĩ")
            clinic = db.execute("SELECT * FROM clinics WHERE id = ?", (prof["clinic_id"],)).fetchone()
            return self.send_json(200, dict(clinic) if clinic else {})

        # /api/clinic/partner/invoices
        if path == "/api/clinic/partner/invoices":
            uid = self.get_authenticated_user_id()
            db = get_db()
            invoices = db.execute("SELECT * FROM partner_invoices ORDER BY created_at DESC LIMIT 20").fetchall()
            return self.send_json(200, [dict(i) for i in invoices])

        # /api/consents
        if path == "/api/consents":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consents.list_user_consents(uid))

        # /api/consents/<id>/chain
        match_consent_chain = re.match(r"^/api/consents/([a-zA-Z0-9_\-]+)/chain$", path)
        if match_consent_chain:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consents.get_consent_chain(uid, match_consent_chain.group(1), ip))

        # /api/consents/<id>
        match_consent = re.match(r"^/api/consents/([a-zA-Z0-9_\-]+)$", path)
        if match_consent:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consents.get_consent(uid, match_consent.group(1), ip))

        # /api/consults/<consentId>/messages
        match_cons = re.match(r"^/api/consults/([a-zA-Z0-9_\-]+)/messages$", path)
        if match_cons:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consults.get_consult_messages(uid, match_cons.group(1)))

        # /api/clinician/inbox
        if path == "/api/clinician/inbox":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, clinician.get_clinician_inbox(uid))

        # /api/clinician/cases/<id>
        match_doc_c = re.match(r"^/api/clinician/cases/([a-zA-Z0-9_\-]+)$", path)
        if match_doc_c:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, clinician.get_case_for_clinician(uid, match_doc_c.group(1)))

        # /api/admin/audit
        if path == "/api/admin/audit":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, admin.get_audit_logs(uid, ip=ip))

        # /api/admin/health
        if path == "/api/admin/health":
            return self.send_json(200, admin.get_system_health())

        # /api/admin/users
        if path == "/api/admin/users":
            uid = self.get_authenticated_user_id()
            enforce_admin(uid, "list_users", ip)
            db = get_db()
            users = db.execute("SELECT id, email, display_name, role, status, created_at FROM users ORDER BY created_at DESC LIMIT 50").fetchall()
            return self.send_json(200, [dict(u) for u in users])

        # /api/admin/clinicians/pending
        if path == "/api/admin/clinicians/pending":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, admin.list_pending_clinicians(uid, ip=ip))

        # /api/chain/transactions
        if path == "/api/chain/transactions":
            return self.send_json(200, chain.list_chain_transactions())

        # /api/wallet
        if path == "/api/wallet":
            uid = "guest"
            try: uid = self.get_authenticated_user_id()
            except Exception: pass
            return self.send_json(200, {
                "address": "0x71C...B29f (Avalanche C-Chain Fuji)",
                "chain_id": 43113,
                "token": "AVAX (Testnet)",
                "balance": 1.25,
                "badge": "DEV WALLET - ZERO REAL VALUE"
            })

        # /api/notifications
        if path == "/api/notifications":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, reminders.list_user_notifications(uid))

        return self.send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Route GET {path} not found", "details": {}}})

    # -------------------------------------------------------------
    # POST DISPATCHER
    # -------------------------------------------------------------
    def dispatch_api_post(self, path: str, body: dict):
        ip = self.get_client_ip()

        # Auth
        if path == "/api/auth/register":
            return self.send_json(201, auth.register_patient(body))

        if path == "/api/auth/register-clinician":
            return self.send_json(201, auth.register_clinician(body))

        if path == "/api/auth/login":
            check_rate_limit(ip, "login")
            return self.send_json(200, auth.login(body))

        if path == "/api/me/privacy-accept":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, auth.accept_privacy(uid, body.get("version", "v1.0")))

        # FIX-02 & FIX-03: Safety Check Endpoint
        if path == "/api/safety/check":
            symptoms = body.get("symptoms", {})
            profile_type = body.get("profile_type", "other")
            facts = dict(symptoms)
            facts["profile_type"] = profile_type
            safety_eval = evaluate_safety_rules(facts)
            return self.send_json(200, safety_eval)

        # FIX-01 & FIX-02: Wizard Analyze Pipeline (End-to-end Step 3)
        if path == "/api/wizard/analyze":
            check_rate_limit(ip, "upload")
            img_b64 = body.get("image_base64", "")
            img_bytes = None
            if img_b64:
                if "," in img_b64:
                    img_b64 = img_b64.split(",", 1)[1]
                try:
                    img_bytes = base64.b64decode(img_b64)
                except Exception:
                    raise ValidationException("Định dạng ảnh base64 không hợp lệ")

            body_site = body.get("body_site", "face")
            profile_type = body.get("profile_type", "other")
            symptoms = body.get("symptoms", {})
            notes = body.get("notes", "")

            # Identify user (guest or authenticated)
            uid = "guest"
            try: uid = self.get_authenticated_user_id()
            except Exception: pass

            case_id = body.get("case_id") or str(uuid.uuid4())
            obs_id = body.get("observation_id") or str(uuid.uuid4())

            # Run complete LangGraph workflow
            workflow_res = run_agent_workflow(
                case_id=case_id,
                observation_id=obs_id,
                user_id=uid,
                body_site=body_site,
                profile_type=profile_type,
                symptoms=symptoms,
                image_bytes=img_bytes,
                user_notes=notes
            )

            # If user is authenticated and quality is not RETAKE, persist observation to DB
            if uid != "guest" and img_bytes and workflow_res["quality"]["status"] != "RETAKE":
                try:
                    db = get_db()
                    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    # Ensure case exists
                    case_row = db.execute("SELECT id FROM cases WHERE id = ?", (case_id,)).fetchone()
                    if not case_row:
                        db.execute(
                            "INSERT INTO cases (id, patient_id, profile_type, body_site, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'active', ?, ?)",
                            (case_id, uid, profile_type, body_site, now_iso, now_iso)
                        )
                    # Create observation
                    db.execute(
                        "INSERT INTO observations (id, case_id, captured_at, workflow_state, created_at, updated_at) VALUES (?, ?, ?, 'ANALYZED', ?, ?)",
                        (obs_id, case_id, now_iso, now_iso, now_iso)
                    )
                    # Upload image asset
                    img_res = images.upload_observation_image(uid, obs_id, img_bytes, view_type="overview", ip=ip)
                    workflow_res["image_id"] = img_res["image_id"]

                    # Persist measurements
                    for m in workflow_res.get("measurements", []):
                        db.execute(
                            """
                            INSERT INTO visual_measurements (id, observation_id, metric_name, value, unit, confidence, model_version, provenance, details, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (str(uuid.uuid4()), obs_id, m["metric_name"], m["value"], m["unit"], m["confidence"], m["model_version"], m["provenance"], json.dumps(m.get("details", {})), now_iso, now_iso)
                        )

                    # Persist similar conditions
                    sim_items = workflow_res.get("similar_conditions", {}).get("items", [])
                    db.execute(
                        """
                        INSERT INTO similar_condition_results (id, observation_id, embedder_version, kb_version, results, abstain_reason, created_at, updated_at)
                        VALUES (?, ?, 'fv-1', 'kb-2026.11-draft1', ?, ?, ?, ?)
                        """,
                        (str(uuid.uuid4()), obs_id,
                         json.dumps([{"slug": s["slug"], "rank_internal": i + 1} for i, s in enumerate(sim_items)]),
                         workflow_res.get("similar_conditions", {}).get("abstain_reason"),
                         now_iso, now_iso)
                    )
                    db.commit()
                except Exception as e:
                    # In-memory result is still returned if persistence failed
                    workflow_res["db_save_error"] = str(e)

            workflow_res["case_id"] = case_id
            workflow_res["observation_id"] = obs_id
            return self.send_json(200, workflow_res)

        # Observations Image Upload
        match_obs_img = re.match(r"^/api/observations/([a-zA-Z0-9_\-]+)/images$", path)
        if match_obs_img:
            uid = self.get_authenticated_user_id()
            check_rate_limit(uid, "upload")
            obs_id = match_obs_img.group(1)
            img_b64 = body.get("image_base64", "")
            if not img_b64:
                raise ValidationException("Thiếu dữ liệu ảnh image_base64")
            if "," in img_b64:
                img_b64 = img_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(img_b64)
            view_type = body.get("view_type", "overview")
            return self.send_json(201, images.upload_observation_image(uid, obs_id, img_bytes, view_type=view_type, ip=ip))

        # Images Token
        match_img_tok = re.match(r"^/api/images/([a-zA-Z0-9_\-]+)/token$", path)
        if match_img_tok:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, images.request_image_token(uid, match_img_tok.group(1), ip=ip))

        # Cases
        if path == "/api/cases":
            uid = self.get_authenticated_user_id()
            return self.send_json(201, cases.create_case(uid, body, ip=ip))

        match_close = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/close$", path)
        if match_close:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.close_case(uid, match_close.group(1), ip=ip))

        match_obs = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/observations$", path)
        if match_obs:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, cases.create_observation(uid, match_obs.group(1), body, ip=ip))

        match_sym = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/symptoms$", path)
        if match_sym:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, cases.add_symptoms(uid, match_sym.group(1), body, ip=ip))

        match_rep = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/reports$", path)
        if match_rep:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, reports.create_report(uid, match_rep.group(1), body.get("audience", "patient"), ip=ip))

        match_comp = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/compare$", path)
        if match_comp:
            uid = self.get_authenticated_user_id()
            case_id = match_comp.group(1)
            check_patient_owns_case(uid, case_id, ip)
            obs_a = body.get("obs_a", {})
            obs_b = body.get("obs_b", {})
            return self.send_json(200, evaluate_comparability(obs_a, obs_b))

        # Consents
        if path == "/api/consents":
            uid = self.get_authenticated_user_id()
            return self.send_json(201, consents.create_consent(uid, body, ip=ip))

        match_rev = re.match(r"^/api/consents/([a-zA-Z0-9_\-]+)/revoke$", path)
        if match_rev:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consents.revoke_consent(uid, match_rev.group(1), ip=ip))

        # Consults
        match_msg = re.match(r"^/api/consults/([a-zA-Z0-9_\-]+)/messages$", path)
        if match_msg:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, consults.send_consult_message(uid, match_msg.group(1), body.get("body", ""), ip=ip))

        # Clinician Review
        match_rev = re.match(r"^/api/clinician/cases/([a-zA-Z0-9_\-]+)/reviews$", path)
        if match_rev:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, clinician.record_clinician_review(uid, match_rev.group(1), body, ip=ip))

        # Partner package purchase
        if path == "/api/clinic/partner/purchase":
            uid = self.get_authenticated_user_id()
            db = get_db()
            prof = db.execute("SELECT clinic_id FROM clinician_profiles WHERE user_id = ?", (uid,)).fetchone()
            if not prof:
                raise ForbiddenException("Bạn không phải bác sĩ quản lý phòng khám")
            days = int(body.get("days", 30))
            return self.send_json(200, clinics.purchase_partner_package(prof["clinic_id"], uid, days=days, ip=ip))

        # Admin verifications
        match_adm_clinician_v = re.match(r"^/api/admin/clinicians/([a-zA-Z0-9_\-]+)/verify$", path)
        if match_adm_clinician_v:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, admin.verify_clinician(uid, match_adm_clinician_v.group(1), "verified", ip=ip))

        match_adm_clinician_r = re.match(r"^/api/admin/clinicians/([a-zA-Z0-9_\-]+)/reject$", path)
        if match_adm_clinician_r:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, admin.verify_clinician(uid, match_adm_clinician_r.group(1), "rejected", ip=ip))

        match_adm_clinic_v = re.match(r"^/api/admin/clinics/([a-zA-Z0-9_\-]+)/verify$", path)
        if match_adm_clinic_v:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, admin.verify_clinic(uid, match_adm_clinic_v.group(1), "verified", ip=ip))

        match_adm_clinic_r = re.match(r"^/api/admin/clinics/([a-zA-Z0-9_\-]+)/reject$", path)
        if match_adm_clinic_r:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, admin.verify_clinic(uid, match_adm_clinic_r.group(1), "rejected", ip=ip))

        # Chain
        if path == "/api/chain/anchor":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, chain.anchor_audit_batch(admin_id=uid))

        return self.send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Route POST {path} not found", "details": {}}})

    # -------------------------------------------------------------
    # PUT DISPATCHER
    # -------------------------------------------------------------
    def dispatch_api_put(self, path: str, body: dict):
        ip = self.get_client_ip()

        # /api/observations/<id>/roi
        match_roi = re.match(r"^/api/observations/([a-zA-Z0-9_\-]+)/roi$", path)
        if match_roi:
            obs_id = match_roi.group(1)
            uid = self.get_authenticated_user_id()
            bbox = body.get("bbox", [0.0, 0.0, 1.0, 1.0])
            db = get_db()
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            db.execute(
                "UPDATE observations SET roi_geometry = ?, updated_at = ? WHERE id = ?",
                (json.dumps({"bbox": bbox}), now_iso, obs_id)
            )
            db.commit()
            record_audit_event(uid, "user", "update_roi", "observation", obs_id, "allow", ip)
            return self.send_json(200, {"observation_id": obs_id, "roi_geometry": {"bbox": bbox}})

        return self.send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Route PUT {path} not found", "details": {}}})

    # -------------------------------------------------------------
    # PATCH DISPATCHER
    # -------------------------------------------------------------
    def dispatch_api_patch(self, path: str, body: dict):
        ip = self.get_client_ip()

        # /api/admin/users/<id>
        match_usr = re.match(r"^/api/admin/users/([a-zA-Z0-9_\-]+)$", path)
        if match_usr:
            uid = self.get_authenticated_user_id()
            enforce_admin(uid, "update_user", ip)
            target_id = match_usr.group(1)
            status = body.get("status")
            role = body.get("role")
            db = get_db()
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if status:
                db.execute("UPDATE users SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso, target_id))
            if role:
                db.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?", (role, now_iso, target_id))
            db.commit()
            record_audit_event(uid, "admin", "update_user", "user", target_id, "allow", ip)
            return self.send_json(200, {"user_id": target_id, "status": status, "role": role})

        return self.send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Route PATCH {path} not found", "details": {}}})

    # -------------------------------------------------------------
    # DELETE DISPATCHER
    # -------------------------------------------------------------
    def dispatch_api_delete(self, path: str):
        ip = self.get_client_ip()

        if path == "/api/me":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, auth.delete_my_data(uid))

        # /api/consents/<id>
        match_consent_del = re.match(r"^/api/consents/([a-zA-Z0-9_\-]+)$", path)
        if match_consent_del:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consents.revoke_consent(uid, match_consent_del.group(1), ip=ip))

        # /api/images/<id>
        match_img_del = re.match(r"^/api/images/([a-zA-Z0-9_\-]+)$", path)
        if match_img_del:
            uid = self.get_authenticated_user_id()
            img_id = match_img_del.group(1)
            db = get_db()
            img = db.execute("SELECT * FROM image_assets WHERE id = ?", (img_id,)).fetchone()
            if not img:
                raise NotFoundException("Ảnh không tồn tại")
            db.execute("DELETE FROM image_assets WHERE id = ?", (img_id,))
            db.commit()
            record_audit_event(uid, "user", "delete_image", "image", img_id, "allow", ip)
            return self.send_json(200, {"deleted_image_id": img_id})

        return self.send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Route DELETE {path} not found", "details": {}}})

def run_server(port: int = 8000):
    server_address = ("0.0.0.0", port)
    httpd = ThreadedHTTPServer(server_address, DermaCareHandler)
    print(f"==================================================")
    print(f" DermaCare Agent Server listening on port {port}")
    print(f" Web UI:  http://localhost:{port}/")
    print(f" API:     http://localhost:{port}/api/")
    print(f" Health:  http://localhost:{port}/health")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
