"""
test_web.py — Automated frontend verification and DOM string scanning.
Enforces:
- No forbidden words ("khỏi", "nặng hơn", "nguy hiểm", "bạn bị mắc", "chắc chắn bị")
- No '%' attached to condition names
- Provenance badges present on metrics
- Mandatory medical disclaimer banners present
- Strict alphabetical ordering on similar conditions panel
- Complete coverage of routes from MASTER_SPEC Section 16
"""
import unittest
import os
import re

class TestWebFrontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.html_path = os.path.join(cls.workspace_root, "apps/web/index.html")
        cls.js_path = os.path.join(cls.workspace_root, "apps/web/js/app.js")
        cls.css_path = os.path.join(cls.workspace_root, "apps/web/css/styles.css")

        with open(cls.html_path, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

        with open(cls.js_path, "r", encoding="utf-8") as f:
            cls.js_content = f.read()

        with open(cls.css_path, "r", encoding="utf-8") as f:
            cls.css_content = f.read()

    def test_mandatory_disclaimer_banner_present(self):
        """Banner cố định không phải chẩn đoán phải có mặt trong index.html và js."""
        self.assertIn("disclaimer-banner", self.html_content)
        self.assertIn("không phải chẩn đoán", self.html_content.lower())
        self.assertIn("không phải chẩn đoán", self.js_content.lower())

    def test_no_forbidden_diagnostic_words(self):
        """Quét chuỗi UI/JS: không được dùng các từ cấm chuẩn y tế."""
        forbidden_terms = [
            "khỏi",
            "nặng hơn",
            "nguy hiểm",
            "bạn bị mắc",
            "chắc chắn bị",
            "chữa dứt điểm"
        ]
        # Check in user-facing message strings (excluding code comments or function identifiers)
        # We search through quoted string literals
        string_literals = re.findall(r'["\'](.*?)["\']', self.js_content)
        for s in string_literals:
            s_lower = s.lower()
            for term in forbidden_terms:
                # If term is in the string, make sure it is not used diagnostically
                self.assertNotIn(term, s_lower, f"Forbidden diagnostic term '{term}' found in UI string: '{s}'")

    def test_similar_conditions_no_percentage_probabilities(self):
        """SimilarConditionsPanel tuyệt đối không có xác suất %, không xếp hạng nặng nhẹ."""
        # Check SimilarConditionsPanel definition in JS
        match = re.search(r'function SimilarConditionsPanel\(.*?\)\s*\{(.*?)\n\}', self.js_content, re.DOTALL)
        self.assertTrue(match, "SimilarConditionsPanel function not found")
        panel_code = match.group(1)
        
        # Must not contain percentage display next to condition
        self.assertNotIn("%", panel_code)
        # Must contain disclaimer
        self.assertIn("disclaimer_similar", panel_code)
        # Must sort alphabetically
        self.assertIn("localeCompare", panel_code)

    def test_provenance_badges_coverage(self):
        """Mọi chỉ số và màn hình phải hỗ trợ 4 provenance layers."""
        self.assertIn("ai_measured", self.js_content)
        self.assertIn("user_reported", self.js_content)
        self.assertIn("clinician_entered", self.js_content)
        self.assertIn("synthetic", self.js_content)

        # Check badge classes in CSS
        self.assertIn(".badge-ai", self.css_content)
        self.assertIn(".badge-user", self.css_content)
        self.assertIn(".badge-clinician", self.css_content)
        self.assertIn(".badge-synthetic", self.css_content)

    def test_body_map_and_anatomical_sites(self):
        """BodyMap component phải hỗ trợ đầy đủ các vị trí giải phẫu chuẩn."""
        sites = ["face", "scalp", "neck", "chest", "back", "abdomen", "arms", "hands", "groin", "legs", "feet"]
        for site in sites:
            self.assertIn(site, self.js_content, f"Site {site} missing from BodyMap")

    def test_section_16_routes_coverage(self):
        """Toàn bộ routes từ Section 16 phải được khai báo trong router."""
        required_routes = [
            "/start",
            "/cases",
            "/about-limits",
            "/privacy",
            "/terms",
            "/clinics",
            "/sharing",
            "/wallet",
            "/doctor/inbox",
            "/doctor/partner",
            "/admin/audit",
            "/admin/system"
        ]
        for route in required_routes:
            self.assertIn(route, self.js_content, f"Route {route} not found in app.js")

    def test_watermark_when_synthetic(self):
        """Màn hình / dữ liệu synthetic phải có watermark rõ ràng."""
        self.assertIn("synthetic-badge", self.css_content)
        self.assertIn("DEMO", self.js_content)

if __name__ == "__main__":
    unittest.main()
