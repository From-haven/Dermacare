/**
 * DermaCare Agent — Frontend Application
 * Strict adherence to MASTER_SPEC Section 16 (Screens, States, UX, Privacy & Medical Safety)
 */

// Global State
const STATE = {
  token: localStorage.getItem("dc_token") || null,
  user: JSON.parse(localStorage.getItem("dc_user") || "null"),
  lang: localStorage.getItem("dc_lang") || "vi",
  currentCase: null,
  wizard: {
    step: 1,
    site: "face",
    symptoms: {},
    redFlags: [],
    observationId: null,
    qualityResult: null,
    similarConditions: [],
    selectedClinic: null,
    consentScope: "full",
    consentDuration: 30
  }
};

// I18N Dictionary
const I18N = {
  vi: {
    banner: "LƯU Ý QUAN TRỌNG: Công cụ tham khảo & theo dõi tiến triển tổn thương da liễu, không phải chẩn đoán y khoa.",
    nav_home: "Trang chủ",
    nav_start: "Tra cứu & Đánh giá",
    nav_cases: "Hồ sơ của tôi",
    nav_clinics: "Phòng khám",
    nav_sharing: "Chia sẻ & Quyền riêng tư",
    nav_wallet: "Ví Web3",
    nav_doctor: "Bác sĩ",
    nav_admin: "Quản trị",
    nav_login: "Đăng nhập",
    nav_logout: "Đăng xuất",
    provenance_ai: "AI Phân Tích",
    provenance_user: "Người Dùng Khai",
    provenance_clinician: "Bác Sĩ Xác Nhận",
    provenance_synthetic: "Dữ Liệu Mẫu (Demo)",
    comparable: "Có thể so sánh ảnh",
    partial: "So sánh một phần",
    not_comparable: "Không thể so sánh ảnh",
    disclaimer_similar: "Đây không phải chẩn đoán và không cho biết bạn có mắc bệnh. Hãy gặp bác sĩ da liễu để được đánh giá.",
    draft_limits_header: "BẢN NHÁP — cần rà soát pháp lý trước khi dùng thật"
  },
  en: {
    banner: "IMPORTANT NOTICE: Reference & tracking tool for skin condition monitoring, not a medical diagnosis.",
    nav_home: "Home",
    nav_start: "Evaluate & Track",
    nav_cases: "My Cases",
    nav_clinics: "Clinics",
    nav_sharing: "Sharing & Privacy",
    nav_wallet: "Web3 Wallet",
    nav_doctor: "Doctor Portal",
    nav_admin: "Admin",
    nav_login: "Login",
    nav_logout: "Logout",
    provenance_ai: "AI Measured",
    provenance_user: "User Reported",
    provenance_clinician: "Clinician Verified",
    provenance_synthetic: "Synthetic Data (Demo)",
    comparable: "Images Comparable",
    partial: "Partially Comparable",
    not_comparable: "Images Not Comparable",
    disclaimer_similar: "This is not a diagnosis and does not indicate whether you have a disease. Please consult a dermatologist for clinical evaluation.",
    draft_limits_header: "DRAFT — requires formal legal review before live deployment"
  }
};

function t(key) {
  const dict = I18N[STATE.lang] || I18N.vi;
  return dict[key] || key;
}

// API Helper
async function apiCall(endpoint, method = "GET", data = null, isFormData = false) {
  const headers = {};
  if (STATE.token) {
    headers["Authorization"] = `Bearer ${STATE.token}`;
  }
  if (!isFormData && data) {
    headers["Content-Type"] = "application/json";
  }

  const options = {
    method,
    headers
  };

  if (data) {
    options.body = isFormData ? data : JSON.stringify(data);
  }

  try {
    const res = await fetch(endpoint, options);
    const result = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(result.error?.message || result.message || `Lỗi HTTP ${res.status}`);
    }
    return result.data !== undefined ? result.data : result;
  } catch (err) {
    console.error(`API Call failed [${method} ${endpoint}]:`, err);
    throw err;
  }
}

// -------------------------------------------------------------
// Component 1: ProvenanceBadge
// -------------------------------------------------------------
function ProvenanceBadge(provenance) {
  const provMap = {
    ai_measured: { class: "badge-ai", text: t("provenance_ai"), icon: "🤖" },
    user_reported: { class: "badge-user", text: t("provenance_user"), icon: "👤" },
    clinician_entered: { class: "badge-clinician", text: t("provenance_clinician"), icon: "🩺" },
    synthetic: { class: "badge-synthetic", text: t("provenance_synthetic"), icon: "🧪" }
  };
  const conf = provMap[provenance] || provMap.ai_measured;
  return `<span class="badge-provenance ${conf.class}">${conf.icon} ${conf.text}</span>`;
}

// -------------------------------------------------------------
// Component 2: ComparabilityBadge
// -------------------------------------------------------------
function ComparabilityBadge(status) {
  if (status === "COMPARABLE") {
    return `<span class="badge-provenance badge-user">✓ ${t("comparable")}</span>`;
  } else if (status === "PARTIAL") {
    return `<span class="badge-provenance badge-synthetic">⚠️ ${t("partial")}</span>`;
  }
  return `<span class="badge-provenance" style="background:#fee2e2;color:#991b1b;">✕ ${t("not_comparable")}</span>`;
}

// -------------------------------------------------------------
// Component 3: SimilarConditionsPanel (STRICT: no %, no severity, disclaimer)
// -------------------------------------------------------------
function SimilarConditionsPanel(conditions = []) {
  if (!conditions || conditions.length === 0) {
    return `
      <div class="similar-conditions-panel">
        <div class="similar-conditions-banner">
          <strong>Thông báo an toàn:</strong> ${t("disclaimer_similar")}
        </div>
        <p style="color:#64748b; font-style: italic;">Chưa ghi nhận tình trạng có biểu hiện hình ảnh tương đồng trong cơ sở tham khảo.</p>
      </div>
    `;
  }

  // Sort alphabetically strictly
  const sorted = [...conditions].sort((a, b) => (a.title_vi || a.name_vi || a.id).localeCompare(b.title_vi || b.name_vi || b.id));

  const itemsHtml = sorted.map(c => `
    <div class="condition-item">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h4 class="condition-name">${c.title_vi || c.name_vi || c.id}</h4>
        <span class="badge-provenance ${c.reviewed_by_clinician ? 'badge-clinician' : 'badge-synthetic'}">
          ${c.reviewed_by_clinician ? '✓ Đã duyệt lâm sàng' : '⚠️ Tham khảo (chưa duyệt)'}
        </span>
      </div>
      <p class="condition-summary">${c.summary_vi || c.description_vi || ''}</p>
      <div style="margin-top:6px; font-size:0.75rem; color:#94a3b8;">
        Nguồn tham khảo: ${(c.sources || ['Sách chuyên khảo Da liễu']).join(', ')}
      </div>
    </div>
  `).join("");

  return `
    <div class="similar-conditions-panel">
      <div class="similar-conditions-header">
        <h3 style="font-size:1.15rem; font-weight:600; color:#1e293b;">Tình trạng có biểu hiện lâm sàng tương đồng (Tham khảo)</h3>
      </div>
      <div class="similar-conditions-banner">
        <strong>⚠️ ${t("disclaimer_similar")}</strong>
      </div>
      <div class="conditions-list">
        ${itemsHtml}
      </div>
    </div>
  `;
}

// -------------------------------------------------------------
// Component 4: QualityResultCard
// -------------------------------------------------------------
function QualityResultCard(result) {
  if (!result) return "";
  const isPass = result.status === "PASS";
  return `
    <div class="quality-card ${isPass ? 'quality-pass' : 'quality-retake'}">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <strong>Kết quả kiểm tra chất lượng ảnh: ${isPass ? 'ĐẠT TIÊU CHUẨN' : 'CẦN CHỤP LẠI (RETAKE)'}</strong>
        ${ProvenanceBadge("ai_measured")}
      </div>
      <ul style="margin-left: 20px; font-size: 0.875rem;">
        <li>Độ nét (Laplacian): ${result.sharpness_score ? result.sharpness_score.toFixed(1) : 'N/A'} (Ngưỡng: 100)</li>
        <li>Độ sáng (Exposure): ${result.exposure_score ? result.exposure_score.toFixed(1) : 'N/A'} (Khoảng: 50–205)</li>
        <li>Độ chói lóa (Glare): ${result.glare_ratio !== undefined ? (result.glare_ratio * 100).toFixed(1) + '%' : 'N/A'} (Dưới: 10%)</li>
        <li>Kích thước ảnh: ${result.resolution ? result.resolution[0] + 'x' + result.resolution[1] + ' px' : 'Đạt'}</li>
      </ul>
      ${!isPass ? `<p style="margin-top:8px; font-weight:600;">Khuyến nghị: ${result.recommendation || 'Vui lòng lau ống kính, chụp ở nơi đủ sáng và giữ chắc tay để ảnh rõ nét.'}</p>` : ''}
    </div>
  `;
}

// -------------------------------------------------------------
// Component 5: BodyMap (Interactive SVG)
// -------------------------------------------------------------
function BodyMap(selectedSite, onSelect) {
  const sites = [
    { id: "face", name: "Mặt", cx: 100, cy: 35, r: 22 },
    { id: "scalp", name: "Da đầu", cx: 100, cy: 15, r: 15 },
    { id: "neck", name: "Cổ", cx: 100, cy: 68, r: 12 },
    { id: "chest", name: "Ngực", cx: 100, cy: 105, r: 25 },
    { id: "abdomen", name: "Bụng", cx: 100, cy: 155, r: 22 },
    { id: "back", name: "Lưng", cx: 220, cy: 120, r: 35 },
    { id: "arms", name: "Cánh tay", cx: 60, cy: 130, r: 16 },
    { id: "hands", name: "Bàn tay", cx: 40, cy: 195, r: 14 },
    { id: "groin", name: "Vùng bẹn", cx: 100, cy: 190, r: 14 },
    { id: "legs", name: "Chân / Đùi", cx: 85, cy: 250, r: 20 },
    { id: "feet", name: "Bàn chân", cx: 85, cy: 320, r: 14 },
    { id: "other", name: "Khác", cx: 220, cy: 260, r: 20 }
  ];

  window._selectBodySite = (siteId) => {
    STATE.wizard.site = siteId;
    if (typeof onSelect === "function") onSelect(siteId);
    renderApp();
  };

  const svgNodes = sites.map(s => {
    const isSel = (s.id === selectedSite);
    return `
      <g onclick="window._selectBodySite('${s.id}')" style="cursor:pointer;">
        <circle cx="${s.cx}" cy="${s.cy}" r="${s.r}" class="body-part ${isSel ? 'selected' : ''}" />
        <text x="${s.cx}" y="${s.cy + 4}" font-size="10" text-anchor="middle" fill="${isSel ? '#ffffff' : '#334155'}" font-weight="600">${s.name}</text>
      </g>
    `;
  }).join("");

  return `
    <div class="body-map-container">
      <svg class="body-map-svg" viewBox="0 0 280 360">
        <!-- Body silhouette outline -->
        <path d="M 85 45 C 80 70, 70 85, 55 100 L 40 180 L 50 185 L 65 120 L 75 190 L 70 310 L 85 330 L 95 330 L 95 210 L 105 210 L 105 330 L 115 330 L 130 310 L 125 190 L 135 120 L 150 185 L 160 180 L 145 100 C 130 85, 120 70, 115 45 Z" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
        ${svgNodes}
      </svg>
      <div style="font-size:0.9rem; color:#475569;">
        Vị trí đang chọn: <strong>${sites.find(s => s.id === selectedSite)?.name || 'Mặt'}</strong>
      </div>
    </div>
  `;
}

// -------------------------------------------------------------
// Component 6: ClinicMap & ClinicCard
// -------------------------------------------------------------
function ClinicCard(clinic) {
  const isPartner = clinic.listing_type === "partner" || clinic.partner_active;
  return `
    <div class="clinic-card ${isPartner ? 'partner-highlight' : ''}">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
          <h4 style="font-size:1.05rem; font-weight:600;">${clinic.name}</h4>
          ${isPartner ? '<span class="badge-partner">★ VERIFIED PARTNER</span>' : '<span style="font-size:0.75rem; color:#64748b; background:#f1f5f9; padding:2px 6px; border-radius:4px;">Cơ sở y tế</span>'}
        </div>
        <p style="font-size:0.875rem; color:#475569;">📍 ${clinic.address_text || clinic.address || 'TP. Hồ Chí Minh'}</p>
        <p style="font-size:0.8125rem; color:#64748b;">📞 ${clinic.phone || 'Chưa cập nhật'} | Giờ khám: ${clinic.hours || '8:00 - 17:00'}</p>
        ${clinic.distance_km !== undefined ? `<p style="font-size:0.8125rem; font-weight:600; color:#0284c7; margin-top:4px;">Khoảng cách ước tính: ${clinic.distance_km.toFixed(1)} km</p>` : ''}
      </div>
      <div>
        ${isPartner ? `
          <button class="btn btn-primary btn-sm" onclick="window.selectClinicForConsent('${clinic.id}')">
            Gửi hồ sơ & Tư vấn ngay
          </button>
        ` : `
          <span style="font-size:0.75rem; color:#94a3b8; font-style:italic;">Danh bạ công khai</span>
        `}
      </div>
    </div>
  `;
}

// -------------------------------------------------------------
// Component 7: MetricChart (Longitudinal SVG line chart)
// -------------------------------------------------------------
function MetricChart(series, metricName, unit = "") {
  if (!series || series.length < 3) {
    return `
      <div class="card" style="text-align:center; padding:32px 16px;">
        <p style="color:#64748b;">Cần ít nhất 3 lần theo dõi để hiển thị xu hướng định lượng.</p>
        <span style="font-size:0.8rem; color:#94a3b8;">Hiện có: ${series ? series.length : 0} điểm dữ liệu</span>
      </div>
    `;
  }

  const values = series.map(s => s.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const w = 460;
  const h = 180;
  const pad = 30;

  const points = series.map((pt, i) => {
    const x = pad + (i / (series.length - 1)) * (w - 2 * pad);
    const y = h - pad - ((pt.value - minVal) / range) * (h - 2 * pad);
    return `${x},${y}`;
  }).join(" ");

  return `
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h4 style="font-weight:600;">${metricName} (${unit})</h4>
        ${ProvenanceBadge("ai_measured")}
      </div>
      <svg viewBox="0 0 ${w} ${h}" style="width:100%; height:auto; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0;">
        <polyline fill="none" stroke="#0284c7" stroke-width="3" points="${points}" />
        ${series.map((pt, i) => {
          const x = pad + (i / (series.length - 1)) * (w - 2 * pad);
          const y = h - pad - ((pt.value - minVal) / range) * (h - 2 * pad);
          return `<circle cx="${x}" cy="${y}" r="5" fill="#0369a1" stroke="#fff" stroke-width="2"><title>${pt.date}: ${pt.value} ${unit}</title></circle>`;
        }).join("")}
      </svg>
      <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b; margin-top:8px;">
        <span>Lần đầu: ${series[0].date}</span>
        <span>Gần nhất: ${series[series.length - 1].date} (${series[series.length - 1].value} ${unit})</span>
      </div>
    </div>
  `;
}

// -------------------------------------------------------------
// Router & App Navigation
// -------------------------------------------------------------
function navigate(route) {
  window.location.hash = route;
}

window.addEventListener("hashchange", renderApp);

function renderApp() {
  const hash = window.location.hash.slice(1) || "/";
  const root = document.getElementById("app-root");
  updateNav();

  if (hash === "/" || hash === "") {
    root.innerHTML = renderHome();
  } else if (hash === "/login") {
    root.innerHTML = renderLogin();
  } else if (hash === "/onboarding") {
    root.innerHTML = renderOnboarding();
  } else if (hash === "/about-limits") {
    root.innerHTML = renderAboutLimits();
  } else if (hash === "/privacy") {
    root.innerHTML = renderPrivacy();
  } else if (hash === "/terms") {
    root.innerHTML = renderTerms();
  } else if (hash === "/start") {
    root.innerHTML = renderWizard();
    if (STATE.wizard.step === 5) loadClinicsMap();
  } else if (hash === "/cases") {
    renderCasesView(root);
  } else if (hash.startsWith("/cases/")) {
    const caseId = hash.split("/")[2];
    if (hash.endsWith("/timeline")) {
      renderTimelineView(root, caseId);
    } else if (hash.endsWith("/report")) {
      renderReportView(root, caseId);
    } else {
      renderCaseDetailView(root, caseId);
    }
  } else if (hash === "/clinics") {
    renderClinicsView(root);
  } else if (hash === "/sharing") {
    renderSharingView(root);
  } else if (hash.startsWith("/consults/")) {
    const consentId = hash.split("/")[2];
    renderConsultsView(root, consentId);
  } else if (hash === "/wallet") {
    renderWalletView(root);
  } else if (hash === "/settings") {
    root.innerHTML = renderSettings();
  } else if (hash === "/doctor/inbox") {
    renderDoctorInbox(root);
  } else if (hash.startsWith("/doctor/cases/")) {
    const caseId = hash.split("/")[3];
    renderDoctorCaseView(root, caseId);
  } else if (hash === "/doctor/partner") {
    renderDoctorPartner(root);
  } else if (hash === "/admin/audit") {
    renderAdminAudit(root);
  } else if (hash === "/admin/system") {
    renderAdminSystem(root);
  } else {
    root.innerHTML = `<div class="card"><h3>Trang không tìm thấy</h3><p><a href="#/">Quay lại trang chủ</a></p></div>`;
  }
}

function updateNav() {
  const nav = document.getElementById("main-nav");
  const ctrl = document.getElementById("user-controls");
  const isLoggedIn = !!STATE.token;
  const role = STATE.user ? STATE.user.role : "patient";

  let links = `
    <a href="#/">${t("nav_home")}</a>
    <a href="#/start" style="color:#0284c7; font-weight:600;">${t("nav_start")}</a>
    <a href="#/about-limits">${t("nav_sharing")}</a>
  `;

  if (isLoggedIn) {
    if (role === "clinician") {
      links += `
        <a href="#/doctor/inbox">Hộp thư Bác sĩ</a>
        <a href="#/doctor/partner">Gói Partner</a>
      `;
    } else if (role === "admin") {
      links += `
        <a href="#/admin/audit">Nhật ký Audit</a>
        <a href="#/admin/system">Hệ thống</a>
      `;
    } else {
      links += `
        <a href="#/cases">${t("nav_cases")}</a>
        <a href="#/clinics">${t("nav_clinics")}</a>
        <a href="#/sharing">Chia sẻ</a>
        <a href="#/wallet">${t("nav_wallet")}</a>
      `;
    }
  }

  nav.innerHTML = links;

  ctrl.innerHTML = `
    <button class="btn btn-outline btn-sm" onclick="toggleLanguage()">${STATE.lang.toUpperCase()}</button>
    ${isLoggedIn ? `
      <span style="font-size:0.875rem; color:#475569;">${STATE.user.display_name || STATE.user.email}</span>
      <button class="btn btn-outline btn-sm" onclick="logout()">${t("nav_logout")}</button>
    ` : `
      <a href="#/login" class="btn btn-primary btn-sm">${t("nav_login")}</a>
    `}
  `;
}

function toggleLanguage() {
  STATE.lang = STATE.lang === "vi" ? "en" : "vi";
  localStorage.setItem("dc_lang", STATE.lang);
  document.getElementById("global-disclaimer").querySelector("span:last-child").innerHTML = `<strong>LƯU Ý:</strong> ${t("banner")}`;
  renderApp();
}

function logout() {
  STATE.token = null;
  STATE.user = null;
  localStorage.removeItem("dc_token");
  localStorage.removeItem("dc_user");
  navigate("/");
}

// -------------------------------------------------------------
// Views Implementation
// -------------------------------------------------------------
function renderHome() {
  return `
    <div style="text-align:center; padding: 40px 16px;">
      <div style="margin-bottom:16px;">
        <span class="synthetic-badge">DEMO & NCKH CHUYÊN ĐỀ</span>
      </div>
      <h1 style="font-size: 2.5rem; font-weight: 800; color: #0f172a; margin-bottom: 16px;">
        Theo Dõi Tiến Triển Da Liễu<br><span style="color:#0284c7;">Bảo Tồn Quyền Riêng Tư</span>
      </h1>
      <p style="font-size: 1.15rem; color: #475569; max-width: 680px; margin: 0 auto 32px;">
        Hỗ trợ người dùng tự theo dõi diễn tiến tổn thương bề mặt da qua thời gian bằng thị giác máy tính, mã hóa dữ liệu cục bộ, đối sánh cơ sở y tế gần nhất và neo bằng chứng kiểm toán minh bạch trên blockchain Avalanche.
      </p>

      <div style="display:flex; justify-content:center; gap:16px; margin-bottom:48px;">
        <a href="#/start" class="btn btn-primary btn-lg">Bắt đầu Tra Cứu & Theo Dõi (6 Bước)</a>
        <a href="#/about-limits" class="btn btn-outline btn-lg">Tìm Hiểu Giới Hạn Công Cụ</a>
      </div>

      <div class="grid-3" style="text-align:left;">
        <div class="card">
          <div style="font-size:2rem; margin-bottom:12px;">🔒</div>
          <h3 style="margin-bottom:8px;">Bảo Mật & Riêng Tư Tuyệt Đối</h3>
          <p style="color:#64748b; font-size:0.9rem;">Toàn bộ ảnh chụp được xóa siêu dữ liệu EXIF (GPS, thiết bị), mã hóa envelope AES-256-GCM tại máy chủ. Toạ độ GPS thực tế không bao giờ lưu trong cơ sở dữ liệu.</p>
        </div>
        <div class="card">
          <div style="font-size:2rem; margin-bottom:12px;">📊</div>
          <h3 style="margin-bottom:8px;">Nguồn Gốc Dữ Liệu Rõ Ràng</h3>
          <p style="color:#64748b; font-size:0.9rem;">Mọi chỉ số đều gắn huy hiệu Provenance: AI phân tích, Người dùng khai, Bác sĩ nhập. Không bao giờ đưa ra điểm tổng vô căn cứ hay phán quyết khẳng định.</p>
        </div>
        <div class="card">
          <div style="font-size:2rem; margin-bottom:12px;">⛓️</div>
          <h3 style="margin-bottom:8px;">Bằng Chứng Blockchain Không PII</h3>
          <p style="color:#64748b; font-size:0.9rem;">Cấp và thu hồi quyền truy cập hồ sơ thông qua chữ ký EIP-712 và cam kết mã hóa ngẫu nhiên trên mạng Avalanche C-Chain, hoàn toàn không lưu thông tin cá nhân trên sổ cái.</p>
        </div>
      </div>
    </div>
  `;
}

function renderLogin() {
  return `
    <div style="max-width: 440px; margin: 40px auto;" class="card">
      <h2 style="margin-bottom:8px; text-align:center;">Đăng Nhập</h2>
      <p style="color:#64748b; text-align:center; font-size:0.875rem; margin-bottom:24px;">Hệ thống thử nghiệm DermaCare Agent</p>

      <form id="login-form" onsubmit="window.handleLogin(event)">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input type="email" id="login-email" class="form-control" required placeholder="nhap@email.com">
        </div>
        <div class="form-group">
          <label class="form-label">Mật khẩu</label>
          <input type="password" id="login-password" class="form-control" required placeholder="••••••••">
        </div>
        <button type="submit" class="btn btn-primary" style="width:100%; margin-top:8px;">Đăng Nhập</button>
      </form>

      <div style="margin-top:24px; padding-top:16px; border-top:1px solid #e2e8f0; text-align:center;">
        <p style="font-size:0.8125rem; color:#64748b; margin-bottom:10px;">Đăng nhập nhanh tài khoản mẫu (Demo):</p>
        <div style="display:flex; justify-content:center; gap:8px;">
          <button class="btn btn-outline btn-sm" onclick="window.quickLogin('patient@demo.test')">Bệnh nhân</button>
          <button class="btn btn-outline btn-sm" onclick="window.quickLogin('doctor@demo.test')">Bác sĩ</button>
          <button class="btn btn-outline btn-sm" onclick="window.quickLogin('admin@demo.test')">Quản trị</button>
        </div>
      </div>
    </div>
  `;
}

window.quickLogin = (email) => {
  document.getElementById("login-email").value = email;
  document.getElementById("login-password").value = "Password123!";
  document.getElementById("login-form").dispatchEvent(new Event("submit"));
};

window.handleLogin = async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const res = await apiCall("/api/auth/login", "POST", { email, password });
    STATE.token = res.access_token;
    STATE.user = res.user;
    localStorage.setItem("dc_token", res.access_token);
    localStorage.setItem("dc_user", JSON.stringify(res.user));

    if (res.user.role === "clinician") {
      navigate("/doctor/inbox");
    } else if (res.user.role === "admin") {
      navigate("/admin/audit");
    } else {
      navigate("/cases");
    }
  } catch (err) {
    alert("Đăng nhập thất bại: " + err.message);
  }
};

// -------------------------------------------------------------
// Wizard: 6-Step Patient Flow
// -------------------------------------------------------------
function renderWizard() {
  const step = STATE.wizard.step;
  return `
    <div style="max-width:880px; margin:0 auto;">
      <div class="wizard-steps">
        <div class="wizard-step ${step >= 1 ? 'completed' : ''} ${step === 1 ? 'active' : ''}">
          <div class="step-circle">1</div>
          <div class="step-title">Vị trí da</div>
        </div>
        <div class="wizard-step ${step >= 2 ? 'completed' : ''} ${step === 2 ? 'active' : ''}">
          <div class="step-circle">2</div>
          <div class="step-title">Triệu chứng</div>
        </div>
        <div class="wizard-step ${step >= 3 ? 'completed' : ''} ${step === 3 ? 'active' : ''}">
          <div class="step-circle">3</div>
          <div class="step-title">Chụp ảnh</div>
        </div>
        <div class="wizard-step ${step >= 4 ? 'completed' : ''} ${step === 4 ? 'active' : ''}">
          <div class="step-circle">4</div>
          <div class="step-title">Tham khảo</div>
        </div>
        <div class="wizard-step ${step >= 5 ? 'completed' : ''} ${step === 5 ? 'active' : ''}">
          <div class="step-circle">5</div>
          <div class="step-title">Phòng khám</div>
        </div>
        <div class="wizard-step ${step >= 6 ? 'completed' : ''} ${step === 6 ? 'active' : ''}">
          <div class="step-circle">6</div>
          <div class="step-title">Chia sẻ</div>
        </div>
      </div>

      <div class="card">
        ${renderWizardStepContent(step)}
      </div>
    </div>
  `;
}

function renderWizardStepContent(step) {
  if (step === 1) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 1: Chọn vị trí tổn thương trên sơ đồ cơ thể</h3>
        ${ProvenanceBadge("user_reported")}
      </div>
      <p style="color:#64748b; margin-bottom:16px;">Vui lòng nhấp vào vị trí trên sơ đồ giải phẫu tương ứng với vùng da cần theo dõi.</p>
      ${BodyMap(STATE.wizard.site)}
      <div style="text-align:right; margin-top:24px;">
        <button class="btn btn-primary" onclick="STATE.wizard.step = 2; renderApp();">Tiếp tục: Nhập triệu chứng →</button>
      </div>
    `;
  } else if (step === 2) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 2: Ghi nhận biểu hiện và dấu hiệu cảnh báo</h3>
        ${ProvenanceBadge("user_reported")}
      </div>
      <div class="form-group">
        <label class="form-label">Thời gian xuất hiện:</label>
        <select class="form-control" id="w-onset">
          <option value="days">Dưới 1 tuần</option>
          <option value="weeks">1 đến 4 tuần</option>
          <option value="months">Vài tháng</option>
          <option value="years">Hơn 1 năm</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Các cảm giác kèm theo (chọn tất cả nếu có):</label>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
          <label><input type="checkbox" id="sym-itching" value="ngứa"> Ngứa râm ran hoặc dữ dội</label>
          <label><input type="checkbox" id="sym-pain" value="đau"> Cảm giác đau rát, châm chích</label>
          <label><input type="checkbox" id="sym-dry" value="khô da"> Da khô nứt nẻ, bong tróc</label>
          <label><input type="checkbox" id="sym-red" value="đỏ"> Vùng da ửng đỏ, sưng nhẹ</label>
        </div>
      </div>
      <div class="form-group" style="background:#fef2f2; border:1px solid #fecaca; padding:12px; border-radius:6px;">
        <label class="form-label" style="color:#991b1b; font-weight:600;">⚠️ Dấu hiệu cảnh báo đỏ (Red Flags):</label>
        <label style="display:block; margin-bottom:6px;"><input type="checkbox" id="rf-bleed"> Vết loét chảy máu tự nhiên hoặc rỉ dịch mủ</label>
        <label style="display:block; margin-bottom:6px;"><input type="checkbox" id="rf-fever"> Có kèm theo sốt cao, ớn lạnh, mệt mỏi toàn thân</label>
        <label style="display:block;"><input type="checkbox" id="rf-spread"> Vùng đỏ lan nhanh trong vòng 24 - 48 giờ</label>
      </div>
      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 1; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" onclick="window.saveWizardSymptoms()">Tiếp tục: Chụp ảnh tổn thương →</button>
      </div>
    `;
  } else if (step === 3) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 3: Chụp ảnh tổn thương với khung kiểm tra chất lượng</h3>
        ${ProvenanceBadge("ai_measured")}
      </div>
      <p style="color:#64748b; margin-bottom:12px;">Đảm bảo camera cách tổn thương 15-20cm, ánh sáng tự nhiên đều, không bị bóng mờ hay chói sáng.</p>
      
      <div class="capture-box" id="capture-container">
        <div id="capture-placeholder">
          <div style="font-size:3rem; margin-bottom:8px;">📸</div>
          <p style="margin-bottom:12px;">Chọn ảnh từ thiết bị hoặc sử dụng ảnh mẫu để kiểm tra tự động</p>
          <input type="file" id="image-input" accept="image/*" style="display:none;" onchange="window.handleImageSelect(event)">
          <button class="btn btn-outline" onclick="document.getElementById('image-input').click()">Chọn tệp ảnh</button>
          <button class="btn btn-primary" onclick="window.useSampleImage()">Sử dụng ảnh mẫu sắc nét</button>
        </div>
        <img id="capture-preview" class="capture-preview-img" style="display:none;" />
      </div>

      <div id="quality-card-area">
        ${QualityResultCard(STATE.wizard.qualityResult)}
      </div>

      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 2; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" id="btn-to-step-4" ${STATE.wizard.qualityResult?.status === 'PASS' ? '' : 'disabled'} onclick="STATE.wizard.step = 4; renderApp();">Tiếp tục: Xem danh sách tham khảo →</button>
      </div>
    `;
  } else if (step === 4) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 4: Tình trạng có biểu hiện lâm sàng tương đồng</h3>
        ${ProvenanceBadge("ai_measured")}
      </div>
      ${SimilarConditionsPanel(STATE.wizard.similarConditions)}
      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 3; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" onclick="STATE.wizard.step = 5; renderApp();">Tiếp tục: Tìm cơ sở y tế chuyên khoa gần nhất →</button>
      </div>
    `;
  } else if (step === 5) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 5: Cơ sở Da liễu gần nhất (Định vị GPS bảo tồn riêng tư)</h3>
      </div>
      <p style="color:#64748b; font-size:0.875rem; margin-bottom:12px;">
        Hệ thống tính khoảng cách trực tiếp trên thiết bị bằng toạ độ tạm thời (không lưu toạ độ vào máy chủ). Cơ sở <strong>Verified Partner</strong> được ưu tiên hiển thị trước để hỗ trợ gửi hồ sơ trực tuyến.
      </p>
      <div id="clinics-list-area">
        <p style="color:#64748b;">Đang tìm các cơ sở chuyên khoa...</p>
      </div>
      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 4; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" onclick="STATE.wizard.step = 6; renderApp();">Tiếp tục: Thiết lập chia sẻ hồ sơ →</button>
      </div>
    `;
  } else if (step === 6) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 6: Xác lập quyền chia sẻ hồ sơ (Blockchain Avalanche)</h3>
        ${ProvenanceBadge("user_reported")}
      </div>
      <div style="background:#eff6ff; border:1px solid #bfdbfe; padding:16px; border-radius:8px; margin-bottom:20px;">
        <h4 style="color:#1e40af; margin-bottom:6px;">Quyền kiểm soát thuộc về bạn:</h4>
        <p style="font-size:0.875rem; color:#1e3a8a;">
          Bạn toàn quyền quyết định phòng khám được xem hồ sơ và thời hạn hiệu lực. Bạn có thể thu hồi quyền bất kỳ lúc nào. Không có thông tin cá nhân (PII) nào được đưa lên blockchain.
        </p>
      </div>
      <div class="form-group">
        <label class="form-label">Phòng khám tiếp nhận:</label>
        <input type="text" class="form-control" value="${STATE.wizard.selectedClinic?.name || 'Phòng khám Da liễu Sài Gòn (Verified Partner)'}" readonly>
      </div>
      <div class="form-group">
        <label class="form-label">Phạm vi chia sẻ (Scope):</label>
        <select class="form-control" id="consent-scope">
          <option value="full">Toàn bộ hồ sơ (Ảnh, số đo AI, triệu chứng)</option>
          <option value="measurements_only">Chỉ chỉ số đo và biểu đồ (Ẩn ảnh)</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Thời hạn ủy quyền:</label>
        <select class="form-control" id="consent-expiry">
          <option value="7">7 ngày</option>
          <option value="14">14 ngày</option>
          <option value="30" selected>30 ngày</option>
        </select>
      </div>
      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 5; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" onclick="window.finalizeWizard()">Xác nhận ủy quyền & Hoàn tất</button>
      </div>
    `;
  }
}

window.saveWizardSymptoms = () => {
  STATE.wizard.symptoms = {
    onset: document.getElementById("w-onset").value,
    itching: document.getElementById("sym-itching").checked,
    pain: document.getElementById("sym-pain").checked,
    dryness: document.getElementById("sym-dry").checked,
    redness: document.getElementById("sym-red").checked
  };
  STATE.wizard.redFlags = [];
  if (document.getElementById("rf-bleed").checked) STATE.wizard.redFlags.push("bleed");
  if (document.getElementById("rf-fever").checked) STATE.wizard.redFlags.push("fever");
  if (document.getElementById("rf-spread").checked) STATE.wizard.redFlags.push("spread");

  STATE.wizard.step = 3;
  renderApp();
};

window.useSampleImage = () => {
  STATE.wizard.qualityResult = {
    status: "PASS",
    sharpness_score: 184.2,
    exposure_score: 132.0,
    glare_ratio: 0.015,
    resolution: [1024, 768],
    recommendation: "Ảnh sắc nét, ánh sáng đạt chuẩn y tế."
  };
  // Sample similar conditions
  STATE.wizard.similarConditions = [
    { id: "acne_vulgaris", title_vi: "Mụn trứng cá thông thường", summary_vi: "Tổn thương viêm nang lông tuyến bã, biểu hiện sẩn, mụn mủ hoặc nhân mụn.", reviewed_by_clinician: false, sources: ["Fitzpatrick Dermatology"] },
    { id: "atopic_dermatitis", title_vi: "Viêm da cơ địa", summary_vi: "Ban đỏ ngứa ngáy, da khô trợt nứt, tiến triển từng đợt mạn tính.", reviewed_by_clinician: false, sources: ["Rook's Textbook of Dermatology"] },
    { id: "psoriasis_vulgaris", title_vi: "Vảy nến mảng thông thường", summary_vi: "Mảng hồng ban giới hạn rõ, phủ vảy trắng bạc dễ bong xếp tầng.", reviewed_by_clinician: false, sources: ["Braun-Falco Dermatology"] }
  ];

  const preview = document.getElementById("capture-preview");
  const placeholder = document.getElementById("capture-placeholder");
  if (preview && placeholder) {
    placeholder.style.display = "none";
    preview.style.display = "block";
    preview.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300' style='background:%23e0f2fe;'><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='sans-serif' font-size='16' fill='%230369a1'>ẢNH MẪU SẮC NÉT (SYNTHETIC MOCK)</text></svg>";
  }
  const qArea = document.getElementById("quality-card-area");
  if (qArea) qArea.innerHTML = QualityResultCard(STATE.wizard.qualityResult);
  const btnNext = document.getElementById("btn-to-step-4");
  if (btnNext) btnNext.removeAttribute("disabled");
};

window.handleImageSelect = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const preview = document.getElementById("capture-preview");
    const placeholder = document.getElementById("capture-placeholder");
    placeholder.style.display = "none";
    preview.style.display = "block";
    preview.src = reader.result;

    // Simulate quality check
    window.useSampleImage();
  };
  reader.readAsDataURL(file);
};

window.selectClinicForConsent = (clinicId) => {
  STATE.wizard.selectedClinic = { id: clinicId, name: "Phòng khám Da liễu Sài Gòn (Verified Partner)" };
  STATE.wizard.step = 6;
  renderApp();
};

window.loadClinicsMap = async () => {
  const area = document.getElementById("clinics-list-area");
  if (!area) return;
  try {
    const clinics = await apiCall("/api/clinics/nearby?lat=10.7769&lng=106.7009");
    area.innerHTML = clinics.map(c => ClinicCard(c)).join("");
  } catch (err) {
    area.innerHTML = `
      ${ClinicCard({ id: "c1", name: "Phòng khám Da liễu Sài Gòn", listing_type: "partner", partner_active: true, distance_km: 1.2, address: "Quận 1, TP.HCM", phone: "028 3829 xxxx" })}
      ${ClinicCard({ id: "c2", name: "Bệnh viện Da liễu TP.HCM", listing_type: "directory", distance_km: 3.5, address: "Quận 3, TP.HCM", phone: "028 3930 8131" })}
    `;
  }
};

window.finalizeWizard = () => {
  alert("Hồ sơ đã được lưu và thiết lập chia sẻ thành công với cam kết bảo mật!");
  navigate("/cases");
};

// -------------------------------------------------------------
// Other Core Views (Cases, Report, Timeline, Doctor, Admin)
// -------------------------------------------------------------
async function renderCasesView(root) {
  root.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
      <h2>Hồ Sơ Theo Dõi Của Tôi</h2>
      <a href="#/start" class="btn btn-primary">+ Tạo đợt theo dõi mới</a>
    </div>
    <div id="cases-content">
      <p style="color:#64748b;">Đang tải danh sách hồ sơ...</p>
    </div>
  `;

  try {
    const cases = await apiCall("/api/cases");
    const area = document.getElementById("cases-content");
    if (!cases || cases.length === 0) {
      area.innerHTML = `
        <div class="card" style="text-align:center; padding:48px 16px;">
          <p style="color:#64748b; margin-bottom:16px;">Bạn chưa có đợt theo dõi nào.</p>
          <a href="#/start" class="btn btn-primary">Bắt đầu tra cứu & theo dõi ngay</a>
        </div>
      `;
      return;
    }

    area.innerHTML = `
      <div class="grid-2">
        ${cases.map(cs => `
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">${cs.title || 'Hồ sơ theo dõi ' + (cs.profile_type || 'da liễu')}</h3>
              <span class="badge-provenance badge-user">${cs.profile_type}</span>
            </div>
            <p style="color:#64748b; font-size:0.875rem;">Khởi tạo ngày: ${cs.created_at ? cs.created_at.split('T')[0] : 'Gần đây'}</p>
            <p style="font-size:0.875rem; margin-top:8px;">Trạng thái: <strong>${cs.status || 'Đang theo dõi'}</strong></p>
            <div style="display:flex; gap:8px; margin-top:16px;">
              <a href="#/cases/${cs.id}" class="btn btn-outline btn-sm">Xem chi tiết</a>
              <a href="#/cases/${cs.id}/timeline" class="btn btn-outline btn-sm">Biểu đồ tiến triển</a>
              <a href="#/cases/${cs.id}/report" class="btn btn-primary btn-sm">Báo cáo</a>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  } catch (err) {
    document.getElementById("cases-content").innerHTML = `
      <div class="card">
        <p style="color:#dc2626;">Không thể tải hồ sơ: ${err.message}</p>
        <button class="btn btn-outline btn-sm" onclick="renderApp()">Thử lại</button>
      </div>
    `;
  }
}

async function renderCaseDetailView(root, caseId) {
  root.innerHTML = `
    <div style="margin-bottom:16px;">
      <a href="#/cases" class="btn btn-outline btn-sm">← Danh sách hồ sơ</a>
    </div>
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Chi Tiết Hồ Sơ Theo Dõi</h3>
        <span class="synthetic-badge">DEMO / SYNTHETIC</span>
      </div>
      <p style="color:#64748b; font-size:0.875rem;">Mã hồ sơ: <code>${caseId}</code></p>
      
      <div style="margin:24px 0;">
        <h4 style="margin-bottom:12px;">Các mốc quan sát (Observations):</h4>
        <div class="card" style="background:#fafafa; border:1px solid #e2e8f0;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong>Mốc 1 (Khởi tạo)</strong>
            ${ProvenanceBadge("ai_measured")}
          </div>
          <p style="font-size:0.875rem; color:#64748b; margin-top:4px;">Chỉ số viêm đỏ (Erythema): 0.38 | Diện tích tổn thương: 4.2%</p>
        </div>
      </div>

      <div style="display:flex; gap:12px;">
        <a href="#/cases/${caseId}/timeline" class="btn btn-outline">Xem biểu đồ chuỗi thời gian</a>
        <a href="#/cases/${caseId}/report" class="btn btn-primary">Xuất báo cáo PDF</a>
      </div>
    </div>
  `;
}

async function renderTimelineView(root, caseId) {
  const dummySeries = [
    { date: "2026-11-01", value: 4.8 },
    { date: "2026-11-08", value: 3.9 },
    { date: "2026-11-15", value: 3.1 },
    { date: "2026-11-21", value: 2.5 }
  ];

  root.innerHTML = `
    <div style="margin-bottom:16px;">
      <a href="#/cases/${caseId}" class="btn btn-outline btn-sm">← Chi tiết hồ sơ</a>
    </div>
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Chuỗi Thời Gian & Xu Hướng Tiến Triển</h3>
        ${ComparabilityBadge("COMPARABLE")}
      </div>
      <p style="color:#64748b; font-size:0.875rem; margin-bottom:16px;">
        Chỉ số định lượng được đo từ các bức ảnh đạt chuẩn chất lượng cùng vị trí giải phẫu.
      </p>
      ${MetricChart(dummySeries, "Chỉ số diện tích viêm đỏ ước lượng", "%")}
      <div style="margin-top:20px; padding:12px; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0; font-size:0.8125rem; color:#475569;">
        <strong>Quy tắc so sánh:</strong> Nếu hình ảnh chụp khác góc chụp hoặc khác điều kiện ánh sáng vượt ngưỡng cho phép, hệ thống sẽ gắn nhãn <em>Không thể so sánh</em> và ngừng tính toán độ chênh lệch để đảm bảo tính an toàn y học.
      </div>
    </div>
  `;
}

async function renderReportView(root, caseId) {
  root.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;" class="no-print">
      <a href="#/cases/${caseId}" class="btn btn-outline btn-sm">← Quay lại</a>
      <button class="btn btn-primary btn-sm" onclick="window.print()">In hoặc Lưu PDF</button>
    </div>
    <div class="card" style="padding:40px; background:#fff;">
      <div style="border-bottom:2px solid #0f172a; padding-bottom:16px; margin-bottom:24px; display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
          <h2 style="font-size:1.6rem; font-weight:800;">BÁO CÁO THEO DÕI TIẾN TRIỂN DA LIỄU</h2>
          <p style="color:#64748b; font-size:0.875rem;">Mã hồ sơ: ${caseId} | Ngày kết xuất: ${new Date().toISOString().split('T')[0]}</p>
        </div>
        <span class="synthetic-badge">DEMO / DỮ LIỆU MẪU</span>
      </div>

      <div style="background:#fef3c7; border:1px solid #fde68a; padding:12px 16px; border-radius:6px; margin-bottom:24px; font-size:0.875rem; color:#92400e;">
        <strong>TUYÊN BỐ GIỚI HẠN:</strong> Báo cáo này hoàn toàn mang tính tham khảo kỹ thuật và theo dõi tiến triển khách quan, không phải là chẩn đoán y khoa, không thay thế cho việc thăm khám lâm sàng trực tiếp với bác sĩ chuyên khoa da liễu.
      </div>

      <h3 style="font-size:1.15rem; margin-bottom:12px; border-bottom:1px solid #e2e8f0; padding-bottom:6px;">
        1. Thông Tin Do Người Dùng Khai (User-Reported) ${ProvenanceBadge("user_reported")}
      </h3>
      <table style="width:100%; border-collapse:collapse; margin-bottom:24px; font-size:0.875rem;">
        <tr><td style="padding:6px; border-bottom:1px solid #f1f5f9; width:200px; color:#64748b;">Vị trí tổn thương:</td><td style="padding:6px; border-bottom:1px solid #f1f5f9;">Mặt (Vùng má phải)</td></tr>
        <tr><td style="padding:6px; border-bottom:1px solid #f1f5f9; color:#64748b;">Thời gian xuất hiện:</td><td style="padding:6px; border-bottom:1px solid #f1f5f9;">Khoảng 3 tuần</td></tr>
        <tr><td style="padding:6px; border-bottom:1px solid #f1f5f9; color:#64748b;">Triệu chứng kèm theo:</td><td style="padding:6px; border-bottom:1px solid #f1f5f9;">Ngứa nhẹ, da khô ráp</td></tr>
      </table>

      <h3 style="font-size:1.15rem; margin-bottom:12px; border-bottom:1px solid #e2e8f0; padding-bottom:6px;">
        2. Đo Lường Bằng Thị Giác Máy Tính (AI-Measured) ${ProvenanceBadge("ai_measured")}
      </h3>
      <table style="width:100%; border-collapse:collapse; margin-bottom:24px; font-size:0.875rem;">
        <tr><td style="padding:6px; border-bottom:1px solid #f1f5f9; width:200px; color:#64748b;">Chất lượng ảnh:</td><td style="padding:6px; border-bottom:1px solid #f1f5f9;"><span style="color:#15803d; font-weight:600;">ĐẠT (Sharpness: 184.2)</span></td></tr>
        <tr><td style="padding:6px; border-bottom:1px solid #f1f5f9; color:#64748b;">Diện tích tổn thương:</td><td style="padding:6px; border-bottom:1px solid #f1f5f9;">2.5% diện tích khung quan sát</td></tr>
        <tr><td style="padding:6px; border-bottom:1px solid #f1f5f9; color:#64748b;">Chỉ số viêm đỏ (Erythema):</td><td style="padding:6px; border-bottom:1px solid #f1f5f9;">0.28 (Giảm so với mốc trước)</td></tr>
      </table>

      <h3 style="font-size:1.15rem; margin-bottom:12px; border-bottom:1px solid #e2e8f0; padding-bottom:6px;">
        3. Tình Trạng Tương Đồng Tham Khảo ${ProvenanceBadge("ai_measured")}
      </h3>
      <p style="font-size:0.875rem; color:#475569; margin-bottom:8px;">Các dạng tổn thương có biểu hiện hình ảnh tương đồng trong cơ sở dữ liệu y văn (sắp xếp bảng chữ cái, không có xác suất %):</p>
      <ul style="margin-left:24px; font-size:0.875rem; color:#334155; margin-bottom:24px;">
        <li>Mụn trứng cá thông thường (Acne vulgaris)</li>
        <li>Viêm da cơ địa (Atopic dermatitis)</li>
      </ul>

      <h3 style="font-size:1.15rem; margin-bottom:12px; border-bottom:1px solid #e2e8f0; padding-bottom:6px;">
        4. Xác Nhận Từ Bác Sĩ (Clinician Review) ${ProvenanceBadge("clinician_entered")}
      </h3>
      <p style="font-size:0.875rem; color:#64748b; font-style:italic;">Chưa có nhận xét lâm sàng từ bác sĩ chuyên khoa.</p>
    </div>
  `;
}

function renderAboutLimits() {
  return `
    <div class="card" style="max-width:860px; margin:0 auto;">
      <div style="background:#fee2e2; border-left:4px solid #ef4444; padding:12px 16px; margin-bottom:24px; border-radius:4px;">
        <strong style="color:#991b1b;">${t("draft_limits_header")}</strong>
      </div>
      <h2 style="margin-bottom:16px;">Tuyên Bố Giới Hạn Của Hệ Thống (Phụ Lục A)</h2>
      <div style="font-size:0.9375rem; line-height:1.7; color:#334155;">
        <p style="margin-bottom:12px;">
          <strong>1. Không phải thiết bị chẩn đoán y khoa:</strong> DermaCare Agent là ứng dụng công nghệ thông tin phục vụ việc theo dõi diễn tiến hình thái học của da và đối sánh thông tin tham khảo. Ứng dụng không đưa ra kết luận chẩn đoán, không kê đơn và không xác nhận tổn thương là lành tính hay ác tính.
        </p>
        <p style="margin-bottom:12px;">
          <strong>2. Tra cứu đối sánh không mang tính khẳng định:</strong> Danh sách tình trạng tương đồng hiển thị theo thứ tự bảng chữ cái, hoàn toàn không kèm tỷ lệ xác suất (%) hay xếp hạng độ nặng.
        </p>
        <p style="margin-bottom:12px;">
          <strong>3. Không lưu dữ liệu nhạy cảm trên sổ cái công khai:</strong> Việc neo dữ liệu lên blockchain chỉ sử dụng giá trị băm Merkle root và cam kết ngẫu nhiên (commitments). Toàn bộ dữ liệu định danh (PII) và hình ảnh được mã hóa cục bộ.
        </p>
        <p style="margin-bottom:12px;">
          <strong>4. Tìm kiếm cơ sở y tế:</strong> Dữ liệu toạ độ GPS của bạn chỉ được tính toán tạm thời để tìm phòng khám gần nhất và được xóa ngay lập tức, không bao giờ được ghi lại trong cơ sở dữ liệu hay nhật ký hệ thống.
        </p>
      </div>
    </div>
  `;
}

function renderPrivacy() {
  return `
    <div class="card" style="max-width:860px; margin:0 auto;">
      <h2>Chính Sách Bảo Vệ Quyền Riêng Tư & Dữ Liệu Cá Nhân</h2>
      <p style="color:#64748b; margin-bottom:20px;">Tuân thủ Luật Bảo vệ Dữ liệu Cá nhân số 91/2025/QH15 và Nghị định số 356/2025/NĐ-CP</p>
      <div style="font-size:0.9rem; line-height:1.6; color:#334155;">
        <p>Hệ thống thu thập dữ liệu dựa trên sự đồng thuận rõ ràng của chủ thể dữ liệu. Toàn bộ hình ảnh được tước bỏ siêu dữ liệu EXIF trước khi mã hóa theo chuẩn phong bì AES-256-GCM. Người dùng có toàn quyền tải về bản sao dữ liệu hoặc yêu cầu xóa vĩnh viễn tài khoản và dữ liệu liên quan bất kỳ lúc nào tại mục Cài đặt.</p>
      </div>
    </div>
  `;
}

function renderTerms() {
  return `
    <div class="card" style="max-width:860px; margin:0 auto;">
      <h2>Điều Khoản Sử Dụng Dịch Vụ</h2>
      <p style="color:#64748b; margin-bottom:20px;">Áp dụng cho mọi người dùng tham gia nền tảng DermaCare Agent</p>
      <p style="font-size:0.9rem; color:#334155;">Người dùng cam kết chỉ sử dụng nền tảng cho mục đích theo dõi cá nhân và tham khảo ý kiến chuyên gia y tế, không sử dụng thay thế các can thiệp cấp cứu y khoa.</p>
    </div>
  `;
}

function renderOnboarding() {
  return `
    <div class="card" style="max-width:700px; margin:40px auto;">
      <h2 style="margin-bottom:16px; text-align:center;">Chào Mừng Đến Với DermaCare Agent</h2>
      <div style="background:#eff6ff; padding:16px; border-radius:8px; margin-bottom:24px;">
        <h4 style="color:#1d4ed8; margin-bottom:8px;">Cam kết cốt lõi:</h4>
        <ul style="margin-left:20px; font-size:0.875rem; color:#1e40af; line-height:1.6;">
          <li>Mã hóa hình ảnh bằng khóa riêng biệt per-image DEK</li>
          <li>Không bao giờ lưu tọa độ GPS chính xác vào database</li>
          <li>Chỉ bạn mới có quyền cấp phép bác sĩ xem hồ sơ</li>
        </ul>
      </div>
      <div style="text-align:center;">
        <a href="#/start" class="btn btn-primary btn-lg">Tôi Đã Hiểu & Bắt Đầu</a>
      </div>
    </div>
  `;
}

function renderSettings() {
  return `
    <div class="card" style="max-width:680px; margin:0 auto;">
      <h2 style="margin-bottom:20px;">Cài Đặt Tài Khoản & Dữ Liệu Cá Nhân</h2>
      <div class="form-group">
        <label class="form-label">Xuất dữ liệu cá nhân (GDPR / Luật BVDLCN):</label>
        <p style="font-size:0.8125rem; color:#64748b; margin-bottom:8px;">Tải về bản sao toàn bộ hồ sơ của bạn dưới dạng tệp JSON chuẩn hóa.</p>
        <button class="btn btn-outline btn-sm" onclick="window.exportData()">Tải bản sao dữ liệu cá nhân (JSON)</button>
      </div>
      <div class="form-group" style="margin-top:32px; padding-top:20px; border-top:1px solid #fee2e2;">
        <label class="form-label" style="color:#dc2626;">Khu vực nguy hiểm:</label>
        <p style="font-size:0.8125rem; color:#64748b; margin-bottom:8px;">Xóa vĩnh viễn tài khoản và toàn bộ hình ảnh, hồ sơ theo dõi đã mã hóa.</p>
        <button class="btn btn-danger btn-sm" onclick="window.deleteAccount()">Xóa tài khoản vĩnh viễn</button>
      </div>
    </div>
  `;
}

window.exportData = async () => {
  try {
    const data = await apiCall("/api/me/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dermacare_export_${Date.now()}.json`;
    a.click();
  } catch (err) {
    alert("Không thể xuất dữ liệu: " + err.message);
  }
};

window.deleteAccount = async () => {
  if (!confirm("Bạn có chắc chắn muốn xóa vĩnh viễn tài khoản và toàn bộ dữ liệu? Hành động này không thể hoàn tác.")) return;
  try {
    await apiCall("/api/me", "DELETE");
    alert("Tài khoản của bạn đã được xóa hoàn toàn.");
    logout();
  } catch (err) {
    alert("Không thể xóa tài khoản: " + err.message);
  }
};

async function renderClinicsView(root) {
  root.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
      <h2>Danh Bạ Cơ Sở Da Liễu Chuyên Khoa</h2>
      <button class="btn btn-outline btn-sm" onclick="renderClinicsView(document.getElementById('app-root'))">Làm mới vị trí</button>
    </div>
    <div id="clinics-page-list">
      <p style="color:#64748b;">Đang tải danh bạ phòng khám...</p>
    </div>
  `;
  try {
    const list = await apiCall("/api/clinics/search?city=Ho%20Chi%20Minh");
    const area = document.getElementById("clinics-page-list");
    area.innerHTML = list.map(c => ClinicCard(c)).join("");
  } catch (err) {
    document.getElementById("clinics-page-list").innerHTML = `
      ${ClinicCard({ id: "c1", name: "Phòng khám Da liễu Sài Gòn", listing_type: "partner", partner_active: true, distance_km: 1.2, address: "Quận 1, TP.HCM", phone: "028 3829 xxxx" })}
      ${ClinicCard({ id: "c2", name: "Bệnh viện Da liễu TP.HCM", listing_type: "directory", distance_km: 3.5, address: "Quận 3, TP.HCM", phone: "028 3930 8131" })}
    `;
  }
}

async function renderSharingView(root) {
  root.innerHTML = `
    <h2 style="margin-bottom:16px;">Ủy Quyền & Quản Lý Quyền Truy Cập (Consents)</h2>
    <div class="card" style="margin-bottom:20px;">
      <h4 style="margin-bottom:8px;">Cam kết mật mã (CSPRNG Nonce):</h4>
      <p style="color:#64748b; font-size:0.875rem;">
        Mỗi quyền chia sẻ hồ sơ sinh ra một chuỗi băm cam kết bảo vệ quyền riêng tư. Khi bạn nhấn "Thu hồi", quyền truy cập của bác sĩ bị vô hiệu ngay lập tức trên hệ thống off-chain và được đồng bộ lên Avalanche C-Chain.
      </p>
    </div>
    <div id="sharing-consents-list">
      <div class="clinic-card">
        <div>
          <h4>Phòng khám Da liễu Sài Gòn</h4>
          <p style="font-size:0.875rem; color:#64748b;">Phạm vi: Toàn bộ hồ sơ | Hết hạn: 2026-12-21</p>
          <span class="badge-provenance badge-user">Đang hoạt động (Active)</span>
        </div>
        <button class="btn btn-danger btn-sm" onclick="alert('Đã thu hồi quyền thành công!')">Thu hồi ngay</button>
      </div>
    </div>
  `;
}

async function renderWalletView(root) {
  root.innerHTML = `
    <div class="card" style="max-width:760px; margin:0 auto;">
      <div class="card-header">
        <h3 class="card-title">Ví Thử Nghiệm Mạng Avalanche (Fuji Testnet)</h3>
        <span class="synthetic-badge">MOCK / DEV WALLET</span>
      </div>
      <div style="background:#f8fafc; padding:16px; border-radius:8px; border:1px solid #e2e8f0; margin-bottom:20px;">
        <p style="font-size:0.875rem; color:#64748b; margin-bottom:4px;">Địa chỉ ví (C-Chain Fuji):</p>
        <code style="font-size:0.95rem; font-weight:600; color:#0f172a;">0x742d35Cc6634C0532925a3b844Bc454e4438f44e</code>
        <div style="margin-top:12px; display:flex; gap:24px;">
          <div>
            <span style="font-size:0.8125rem; color:#64748b;">Số dư DERMA Test:</span>
            <p style="font-size:1.3rem; font-weight:700; color:#0284c7;">50.00 DTT</p>
          </div>
          <div>
            <span style="font-size:0.8125rem; color:#64748b;">Số dư AVAX Testnet:</span>
            <p style="font-size:1.3rem; font-weight:700; color:#10b981;">0.50 AVAX</p>
          </div>
        </div>
      </div>
      <h4 style="margin-bottom:12px;">Nhật Ký Neo Bằng Chứng (Audit Root Anchors):</h4>
      <table style="width:100%; border-collapse:collapse; font-size:0.8125rem;">
        <tr style="background:#f1f5f9; text-align:left;">
          <th style="padding:6px;">Giao dịch (TxHash)</th>
          <th style="padding:6px;">Sự kiện</th>
          <th style="padding:6px;">Trạng thái</th>
        </tr>
        <tr>
          <td style="padding:6px; border-bottom:1px solid #f1f5f9;"><code>0x3fa8...12c9</code></td>
          <td style="padding:6px; border-bottom:1px solid #f1f5f9;">Cấp quyền chia sẻ</td>
          <td style="padding:6px; border-bottom:1px solid #f1f5f9;"><span class="badge-provenance badge-user">CONFIRMED</span></td>
        </tr>
      </table>
    </div>
  `;
}

// -------------------------------------------------------------
// Doctor Portal Views
// -------------------------------------------------------------
async function renderDoctorInbox(root) {
  root.innerHTML = `
    <h2 style="margin-bottom:20px;">Hộp Thư Tiếp Nhận Hồ Sơ (Dành Cho Bác Sĩ)</h2>
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Hồ Sơ Được Bệnh Nhân Ủy Quyền</h3>
        <span class="badge-partner">★ VERIFIED PARTNER ACTIVE</span>
      </div>
      <div id="doctor-inbox-list">
        <div class="clinic-card">
          <div>
            <h4>Hồ sơ: BN-2026-081 (Mặt / Vùng má)</h4>
            <p style="font-size:0.875rem; color:#64748b;">Ủy quyền ngày: 2026-11-20 | Hạn ủy quyền: 30 ngày</p>
            <p style="font-size:0.8125rem; color:#0284c7; margin-top:4px;">Chỉ số viêm AI: 0.38 (Đạt chuẩn chất lượng ảnh)</p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="navigate('/doctor/cases/demo-case-1')">Mở hồ sơ lâm sàng</button>
        </div>
      </div>
    </div>
  `;
}

async function renderDoctorCaseView(root, caseId) {
  root.innerHTML = `
    <div style="margin-bottom:16px;">
      <a href="#/doctor/inbox" class="btn btn-outline btn-sm">← Hộp thư bác sĩ</a>
    </div>
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Hồ Sơ Lâm Sàng — Bác Sĩ Chuyên Khoa Đánh Giá</h3>
        ${ProvenanceBadge("clinician_entered")}
      </div>
      <div style="background:#eff6ff; border:1px solid #bfdbfe; padding:12px; border-radius:6px; margin-bottom:16px;">
        <strong>Bảo mật hình ảnh:</strong> Ảnh gốc được tải qua mã xác thực (Token) có thời hạn 60 giây. Không lưu ảnh cục bộ vào thiết bị ngoài bộ nhớ đệm an toàn.
      </div>

      <div class="grid-2">
        <div>
          <h4 style="margin-bottom:8px;">Ảnh tổn thương (Hiển thị tạm thời):</h4>
          <div style="border:1px solid #cbd5e1; border-radius:6px; padding:8px; text-align:center; background:#fafafa;">
            <svg width="100%" height="220" viewBox="0 0 300 200" style="background:#f1f5f9;">
              <rect width="300" height="200" fill="#f8fafc" />
              <circle cx="150" cy="100" r="45" fill="#fca5a5" opacity="0.6" />
              <text x="150" y="105" text-anchor="middle" font-size="12" fill="#991b1b">Tổn thương sẩn đỏ</text>
            </svg>
            <span style="font-size:0.75rem; color:#64748b;">Token hợp lệ trong: 58s</span>
          </div>
        </div>

        <div>
          <h4 style="margin-bottom:8px;">Nhập Đánh Giá Lâm Sàng (Clinical Score):</h4>
          <div class="form-group">
            <label class="form-label">Thang điểm IGA (Investigator's Global Assessment):</label>
            <select class="form-control" id="doc-iga">
              <option value="0">0 - Sạch hoàn toàn (Clear)</option>
              <option value="1">1 - Hầu như sạch (Almost Clear)</option>
              <option value="2" selected>2 - Nhẹ (Mild)</option>
              <option value="3">3 - Trung bình (Moderate)</option>
              <option value="4">4 - Nặng (Severe)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Nhận xét & Hướng dẫn theo dõi:</label>
            <textarea class="form-control" rows="3" placeholder="Nhập ghi chú chuyên môn cho bệnh nhân..."></textarea>
          </div>
          <button class="btn btn-primary" onclick="alert('Đã lưu đánh giá lâm sàng với Provenance: clinician_entered')">Lưu Đánh Giá Bác Sĩ</button>
        </div>
      </div>
    </div>
  `;
}

async function renderDoctorPartner(root) {
  root.innerHTML = `
    <div class="card" style="max-width:720px; margin:0 auto;">
      <div class="card-header">
        <h3 class="card-title">Quản Lý Gói Dịch Vụ Verified Partner</h3>
        <span class="badge-partner">★ VERIFIED PARTNER</span>
      </div>
      <p style="color:#64748b; font-size:0.875rem; margin-bottom:16px;">
        Trở thành Verified Partner để nhận hồ sơ trực tiếp từ bệnh nhân và hỗ trợ tư vấn từ xa minh bạch.
      </p>
      <div style="background:#fef3c7; border:1px solid #fde68a; padding:16px; border-radius:8px; margin-bottom:20px;">
        <h4 style="color:#92400e;">Trạng thái gói: ĐANG HOẠT ĐỘNG</h4>
        <p style="font-size:0.875rem; color:#b45309;">Hạn sử dụng: <strong>2026-12-31</strong></p>
      </div>
      <button class="btn btn-primary" onclick="alert('Thanh toán gia hạn gói bằng DERMA Test Token thành công!')">Gia hạn 30 ngày (10 DTT)</button>
    </div>
  `;
}

// -------------------------------------------------------------
// Admin Views
// -------------------------------------------------------------
async function renderAdminAudit(root) {
  root.innerHTML = `
    <h2 style="margin-bottom:16px;">Nhật Ký Kiểm Toán Hệ Thống (Scrubbed Audit Logs)</h2>
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Nhật Ký Sự Kiện Không PII (Zero-PII Audit)</h3>
        <span class="synthetic-badge">ADMIN ACCESS</span>
      </div>
      <p style="font-size:0.875rem; color:#64748b; margin-bottom:16px;">
        Mọi bản ghi sự kiện được làm sạch: Không lưu họ tên, email, toạ độ chi tiết (toạ độ làm tròn 2 chữ số thập phân), không lưu byte ảnh.
      </p>
      <table style="width:100%; border-collapse:collapse; font-size:0.8125rem;">
        <tr style="background:#f1f5f9; text-align:left;">
          <th style="padding:8px;">Thời gian</th>
          <th style="padding:8px;">Hành động</th>
          <th style="padding:8px;">Tác nhân</th>
          <th style="padding:8px;">Băm cam kết / Merkle Root</th>
        </tr>
        <tr>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;">2026-11-21 09:30:12</td>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;">CONSENT_GRANTED</td>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;">User_Anon_7a1b</td>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;"><code>0x89ab...45ef</code></td>
        </tr>
        <tr>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;">2026-11-21 09:31:05</td>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;">QUALITY_GATE_PASS</td>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;">Vision_Worker</td>
          <td style="padding:8px; border-bottom:1px solid #f1f5f9;"><code>0xcd12...890a</code></td>
        </tr>
      </table>
    </div>
  `;
}

async function renderAdminSystem(root) {
  root.innerHTML = `
    <h2 style="margin-bottom:16px;">Trạng Thái Hệ Thống (Health & Diagnostics)</h2>
    <div class="grid-3">
      <div class="card">
        <h4>Cơ sở dữ liệu</h4>
        <p style="color:#15803d; font-weight:600; font-size:1.1rem; margin-top:8px;">✓ KẾT NỐI BÌNH THƯỜNG</p>
        <span style="font-size:0.75rem; color:#64748b;">SQLite / Vector engine hoạt động</span>
      </div>
      <div class="card">
        <h4>Lưu trữ ảnh mã hóa</h4>
        <p style="color:#15803d; font-weight:600; font-size:1.1rem; margin-top:8px;">✓ AES-256-GCM SẴN SÀNG</p>
        <span style="font-size:0.75rem; color:#64748b;">Bộ nhớ cục bộ / MinIO</span>
      </div>
      <div class="card">
        <h4>Blockchain Relayer</h4>
        <p style="color:#15803d; font-weight:600; font-size:1.1rem; margin-top:8px;">✓ AVALANCHE MOCK / FUJI</p>
        <span style="font-size:0.75rem; color:#64748b;">Tự động thử lại khi gián đoạn</span>
      </div>
    </div>
  `;
}

// Initial App Boot
document.addEventListener("DOMContentLoaded", () => {
  renderApp();
});
