"""
main.py — DermaCare Agent Unified HTTP API & Web Dispatcher Server.
Serves:
- REST API under /api/... and /health
- Web Application & Static Assets from apps/web/
"""
import sys
import os
import re
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Add workspace and apps/api to path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "apps/api"))
sys.path.insert(0, WORKSPACE_ROOT)

from app.config import settings
from app.errors import DermaCareException, UnauthenticatedException
from app.core.security import decode_access_token

# Import routers
from app.routers import (
    auth, cases, images, reports, clinics, consents,
    consults, clinician, admin, chain, reminders
)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class DermaCareHandler(BaseHTTPRequestHandler):
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
        except Exception as e:
            self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "File not found"}})

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
                "timestamp": settings.CHAIN_MODE
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
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e)}})

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
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e)}})

        self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "Endpoint not found"}})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/me":
            try:
                uid = self.get_authenticated_user_id()
                res = auth.delete_my_data(uid)
                return self.send_json(200, res)
            except DermaCareException as de:
                return self.send_json(de.status_code, de.to_dict())
            except Exception as e:
                return self.send_json(500, {"error": {"code": "INTERNAL_ERROR", "message": str(e)}})

        self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "Endpoint not found"}})

    def dispatch_api_get(self, path: str, query: dict):
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

        # /api/cases
        if path == "/api/cases":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.list_user_cases(uid))

        match_case = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)$", path)
        if match_case:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.get_case(uid, match_case.group(1)))

        match_sym = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/symptoms$", path)
        if match_sym:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.get_case_symptoms(uid, match_sym.group(1)))

        # /api/reports/<id>
        match_rep = re.match(r"^/api/reports/([a-zA-Z0-9_\-]+)$", path)
        if match_rep:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, reports.get_report(match_rep.group(1), uid))

        # /api/clinics/nearby
        if path == "/api/clinics/nearby":
            lat = float(query.get("lat", [10.7769])[0])
            lng = float(query.get("lng", [106.7009])[0])
            radius = float(query.get("radius_km", [10.0])[0])
            uid = "guest"
            try: uid = self.get_authenticated_user_id()
            except Exception: pass
            return self.send_json(200, clinics.get_nearby_clinics_endpoint(lat, lng, radius, user_id=uid))

        # /api/clinics/search
        if path == "/api/clinics/search":
            district = query.get("district", [None])[0]
            city = query.get("city", [None])[0]
            return self.send_json(200, clinics.search_clinics_endpoint(district=district, city=city))

        # /api/consents
        if path == "/api/consents":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consents.list_user_consents(uid))

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
            return self.send_json(200, admin.get_audit_logs(uid))

        # /api/admin/health
        if path == "/api/admin/health":
            return self.send_json(200, admin.get_system_health())

        # /api/chain/transactions
        if path == "/api/chain/transactions":
            return self.send_json(200, chain.list_chain_transactions())

        # /api/notifications
        if path == "/api/notifications":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, reminders.list_user_notifications(uid))

        return self.send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Route GET {path} not found"}})

    def dispatch_api_post(self, path: str, body: dict):
        # Auth
        if path == "/api/auth/register":
            return self.send_json(201, auth.register_patient(body))

        if path == "/api/auth/register-clinician":
            return self.send_json(201, auth.register_clinician(body))

        if path == "/api/auth/login":
            return self.send_json(200, auth.login(body))

        if path == "/api/me/privacy-accept":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, auth.accept_privacy(uid, body.get("version", "v1.0")))

        # Cases
        if path == "/api/cases":
            uid = self.get_authenticated_user_id()
            return self.send_json(201, cases.create_case(uid, body))

        match_close = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/close$", path)
        if match_close:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, cases.close_case(uid, match_close.group(1)))

        match_obs = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/observations$", path)
        if match_obs:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, cases.create_observation(uid, match_obs.group(1), body))

        match_sym = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/symptoms$", path)
        if match_sym:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, cases.add_symptoms(uid, match_sym.group(1), body))

        match_rep = re.match(r"^/api/cases/([a-zA-Z0-9_\-]+)/reports$", path)
        if match_rep:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, reports.create_report(uid, match_rep.group(1), body.get("audience", "patient")))

        # Consents
        if path == "/api/consents":
            uid = self.get_authenticated_user_id()
            return self.send_json(201, consents.create_consent(uid, body))

        match_rev = re.match(r"^/api/consents/([a-zA-Z0-9_\-]+)/revoke$", path)
        if match_rev:
            uid = self.get_authenticated_user_id()
            return self.send_json(200, consents.revoke_consent(uid, match_rev.group(1)))

        # Consults
        match_msg = re.match(r"^/api/consults/([a-zA-Z0-9_\-]+)/messages$", path)
        if match_msg:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, consults.send_consult_message(uid, match_msg.group(1), body.get("body", "")))

        # Clinician Review
        match_rev = re.match(r"^/api/clinician/cases/([a-zA-Z0-9_\-]+)/reviews$", path)
        if match_rev:
            uid = self.get_authenticated_user_id()
            return self.send_json(201, clinician.record_clinician_review(uid, match_rev.group(1), body))

        # Chain
        if path == "/api/chain/anchor":
            uid = self.get_authenticated_user_id()
            return self.send_json(200, chain.anchor_audit_batch(admin_id=uid))

        return self.send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Route POST {path} not found"}})

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
