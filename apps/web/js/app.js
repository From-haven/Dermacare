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
    profileType: "other",
    symptoms: {},
    redFlags: [],
    caseId: null,
    observationId: null,
    qualityResult: null,
    measurements: [],
    previewSrc: null,
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
    provenance_synthetic: "Dữ Liệu Mẫu (DEMO / SYNTHETIC)",
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
      const errMsg = result.error?.message || result.message || `Lỗi HTTP ${res.status}`;
      throw new Error(errMsg);
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
  const sorted = [...conditions].sort((a, b) => (a.title_vi || a.name_vi || a.id || "").localeCompare(b.title_vi || b.name_vi || b.id || ""));

  const itemsHtml = sorted.map(c => `
    <div class="condition-item">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h4 class="condition-name">${c.title_vi || c.name_vi || c.id}</h4>
        <span class="badge-provenance ${c.reviewed_by_clinician ? 'badge-clinician' : 'badge-synthetic'}">
          ${c.reviewed_by_clinician ? '✓ Đã duyệt lâm sàng' : '⚠️ Tham khảo (chưa duyệt)'}
        </span>
      </div>
      <p class="condition-summary">${c.summary_vi || c.summary || c.description_vi || ''}</p>
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
  const isPass = result.status === "PASS" || result.status === "REVIEW";
  const metrics = result.metrics || {};
  const retakeSharpness = result.thresholds?.sharpness_retake || 15;
  return `
    <div class="quality-card ${isPass ? 'quality-pass' : 'quality-retake'}">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <strong>Kết quả kiểm tra chất lượng ảnh: ${isPass ? 'ĐẠT TIÊU CHUẨN' : 'CẦN CHỤP LẠI (RETAKE)'}</strong>
        ${ProvenanceBadge("ai_measured")}
      </div>
      <ul style="margin-left: 20px; font-size: 0.875rem;">
        <li>Độ nét (Laplacian): ${metrics.sharpness_score !== undefined ? Number(metrics.sharpness_score).toFixed(1) : (result.sharpness_score || 'N/A')} (Ngưỡng đạt: ${retakeSharpness})</li>
        <li>Tỷ lệ thiếu/thừa sáng: ${metrics.exposure_bad_pct !== undefined ? Number(metrics.exposure_bad_pct).toFixed(1) + '%' : (result.exposure_score ? Number(result.exposure_score).toFixed(1) : 'N/A')}</li>
        <li>Tỷ lệ chói lóa: ${metrics.glare_pct !== undefined ? Number(metrics.glare_pct).toFixed(1) + '%' : (result.glare_ratio !== undefined ? (result.glare_ratio * 100).toFixed(1) + '%' : 'N/A')}</li>
        <li>Khung hình ROI: ${metrics.roi_area_ratio !== undefined ? Number(metrics.roi_area_ratio * 100).toFixed(1) + '%' : 'Đạt'}</li>
      </ul>
      ${result.reasons && result.reasons.length > 0 ? `
        <div style="margin-top:8px; font-weight:600; color:#991b1b;">
          Lý do: ${result.reasons.join("; ")}
        </div>
      ` : ''}
      ${!isPass ? `<p style="margin-top:6px; font-weight:600;">Khuyến nghị: ${result.recommendation || 'Vui lòng giữ chắc tay cách 15-20cm, điều chỉnh ánh sáng tự nhiên đều và tránh chói đèn.'}</p>` : ''}
    </div>
  `;
}

// -------------------------------------------------------------
// Component 5: BodyMap (Interactive SVG with 12 valid anatomical sites)
// -------------------------------------------------------------
function BodyMap(selectedSite, onSelect) {
  const sites = [
    { id: "face", name: "Mặt", cx: 100, cy: 35, r: 22, body_site: "face" },
    { id: "scalp", name: "Da đầu", cx: 100, cy: 15, r: 15, body_site: "scalp" },
    { id: "neck", name: "Cổ", cx: 100, cy: 68, r: 12, body_site: "neck" },
    { id: "chest", name: "Ngực", cx: 100, cy: 110, r: 22, body_site: "trunk_front" },
    { id: "abdomen", name: "Bụng", cx: 100, cy: 155, r: 20, body_site: "trunk_front" },
    { id: "back", name: "Lưng", cx: 220, cy: 120, r: 35, body_site: "back" },
    { id: "arms", name: "Cánh tay", cx: 60, cy: 130, r: 16, body_site: "arms" },
    { id: "hands", name: "Bàn tay", cx: 40, cy: 195, r: 14, body_site: "hands" },
    { id: "groin", name: "Vùng nếp gấp / bẹn", cx: 100, cy: 190, r: 14, body_site: "folds" },
    { id: "legs", name: "Chân / Đùi", cx: 85, cy: 250, r: 20, body_site: "legs" },
    { id: "feet", name: "Bàn chân", cx: 85, cy: 320, r: 14, body_site: "feet" },
    { id: "nails", name: "Móng", cx: 220, cy: 200, r: 14, body_site: "nails" },
    { id: "other", name: "Khác", cx: 220, cy: 260, r: 20, body_site: "other" }
  ];

  window._selectBodySite = (siteId, mappedSite) => {
    STATE.wizard.site = mappedSite || siteId;
    STATE.wizard.selectedSiteId = siteId;
    // Local DOM update for zero lag
    document.querySelectorAll(".body-part").forEach(el => el.classList.remove("selected"));
    const activeCircle = document.getElementById(`circle-${siteId}`);
    if (activeCircle) activeCircle.classList.add("selected");
    const label = document.getElementById("selected-site-label");
    const found = sites.find(s => s.id === siteId);
    if (label && found) label.innerText = found.name;
    if (typeof onSelect === "function") onSelect(mappedSite || siteId);
  };

  const svgNodes = sites.map(s => {
    const isSel = (STATE.wizard.selectedSiteId ? STATE.wizard.selectedSiteId === s.id : (STATE.wizard.site === s.body_site || STATE.wizard.site === s.id));
    return `
      <g onclick="window._selectBodySite('${s.id}', '${s.body_site}')" style="cursor:pointer;" id="node-${s.id}">
        <circle id="circle-${s.id}" cx="${s.cx}" cy="${s.cy}" r="${s.r}" class="body-part ${isSel ? 'selected' : ''}" />
        <text x="${s.cx}" y="${s.cy + 4}" font-size="10" text-anchor="middle" fill="${isSel ? '#ffffff' : '#334155'}" font-weight="600">${s.name.split('/')[0].trim()}</text>
      </g>
    `;
  }).join("");

  const currentLabel = sites.find(s => s.body_site === STATE.wizard.site || s.id === STATE.wizard.site)?.name || "Mặt";

  return `
    <div class="body-map-container">
      <svg class="body-map-svg" viewBox="0 0 280 360">
        <!-- Body silhouette outline -->
        <path d="M 85 45 C 80 70, 70 85, 55 100 L 40 180 L 50 185 L 65 120 L 75 190 L 70 310 L 85 330 L 95 330 L 95 210 L 105 210 L 105 330 L 115 330 L 130 310 L 125 190 L 135 120 L 150 185 L 160 180 L 145 100 C 130 85, 120 70, 115 45 Z" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
        ${svgNodes}
      </svg>
      <div style="font-size:0.95rem; color:#334155; margin-top:8px;">
        Vị trí đang chọn: <strong id="selected-site-label" style="color:#0284c7;">${currentLabel}</strong>
      </div>
    </div>
  `;
}

// -------------------------------------------------------------
// Component 6: ClinicCard
// -------------------------------------------------------------
function ClinicCard(clinic) {
  const isPartner = clinic.listing_type === "partner" || clinic.partner_active;
  return `
    <div class="clinic-card ${isPartner ? 'partner-highlight' : ''}">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
          <h4 style="font-size:1.05rem; font-weight:600;">${clinic.name}</h4>
          ${isPartner ? '<span class="badge-partner">★ VERIFIED PARTNER</span>' : '<span style="font-size:0.75rem; color:#64748b; background:#f1f5f9; padding:2px 6px; border-radius:4px;">Danh bạ công khai</span>'}
        </div>
        ${isPartner ? '<p style="font-size:0.8125rem; font-weight:600; color:#15803d; margin-bottom:4px;">Đối tác xác thực — hiển thị ưu tiên theo gói đối tác</p>' : ''}
        <p style="font-size:0.875rem; color:#475569;">📍 ${clinic.address_text || clinic.address || 'TP. Hồ Chí Minh'}</p>
        <p style="font-size:0.8125rem; color:#64748b;">📞 ${clinic.phone || 'Chưa cập nhật'} | Giờ khám: ${clinic.hours || clinic.hours_note || '8:00 - 17:00'}</p>
        ${clinic.distance_km !== undefined ? `<p style="font-size:0.8125rem; font-weight:600; color:#0284c7; margin-top:4px;">Khoảng cách ước tính: ${Number(clinic.distance_km).toFixed(1)} km</p>` : ''}
      </div>
      <div>
        ${isPartner ? `
          <button class="btn btn-primary btn-sm" onclick="window.selectClinicForConsent('${clinic.id}')">
            Chọn phòng khám & Gửi hồ sơ
          </button>
        ` : `
          <span style="font-size:0.75rem; color:#94a3b8; font-style:italic;">Chỉ liên hệ trực tiếp</span>
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
        <p style="color:#64748b;">Cần ít nhất 3 lần theo dõi đạt tiêu chuẩn để hiển thị xu hướng định lượng.</p>
        <span style="font-size:0.8rem; color:#94a3b8;">Hiện có: ${series ? series.length : 0} điểm dữ liệu</span>
      </div>
    `;
  }

  const values = series.map(s => Number(s.value || 0));
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const w = 460;
  const h = 180;
  const pad = 30;

  const points = series.map((pt, i) => {
    const x = pad + (i / (series.length - 1)) * (w - 2 * pad);
    const y = h - pad - ((Number(pt.value) - minVal) / range) * (h - 2 * pad);
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
          const y = h - pad - ((Number(pt.value) - minVal) / range) * (h - 2 * pad);
          return `<circle cx="${x}" cy="${y}" r="5" fill="#0369a1" stroke="#fff" stroke-width="2"><title>${pt.date || pt.captured_at}: ${pt.value} ${unit}</title></circle>`;
        }).join("")}
      </svg>
      <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b; margin-top:8px;">
        <span>Lần đầu: ${series[0].date || series[0].captured_at}</span>
        <span>Gần nhất: ${series[series.length - 1].date || series[series.length - 1].captured_at} (${series[series.length - 1].value} ${unit})</span>
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
  if (typeof window.stopCameraStream === "function") {
    window.stopCameraStream();
  }
  const hash = window.location.hash.slice(1) || "/";
  const root = document.getElementById("app-root");
  updateNav();

  if (hash === "/" || hash === "") {
    root.innerHTML = renderHome();
  } else if (hash === "/login") {
    root.innerHTML = renderLogin();
  } else if (hash === "/register") {
    root.innerHTML = renderRegister();
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
    if (STATE.wizard.step === 5) {
      if (STATE.deviceGps) {
        window.loadClinicsMap(STATE.deviceGps.lat, STATE.deviceGps.lng, true);
      } else {
        window.getUserLocation(false);
      }
    }
  } else if (hash === "/cases") {
    renderCasesView(root);
  } else if (hash.startsWith("/cases/")) {
    const parts = hash.split("/");
    const caseId = parts[2];
    if (parts[3] === "timeline") {
      renderTimelineView(root, caseId);
    } else if (parts[3] === "report") {
      renderReportView(root, caseId);
    } else {
      renderCaseDetailView(root, caseId);
    }
  } else if (hash === "/clinics") {
    renderClinicsView(root);
  } else if (hash === "/sharing") {
    renderSharingView(root);
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
  } else if (hash === "/admin/verification") {
    renderAdminVerification(root);
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
        <a href="#/admin/verification">Duyệt Bác sĩ & PK</a>
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
      <a href="#/register" class="btn btn-outline btn-sm" style="font-weight:600; border-color:#0284c7; color:#0284c7;">Đăng ký</a>
      <a href="#/login" class="btn btn-primary btn-sm">${t("nav_login")}</a>
    `}
  `;
}

function toggleLanguage() {
  STATE.lang = STATE.lang === "vi" ? "en" : "vi";
  localStorage.setItem("dc_lang", STATE.lang);
  renderApp();
}

function logout() {
  STATE.token = null;
  STATE.user = null;
  localStorage.removeItem("dc_token");
  localStorage.removeItem("dc_user");
  navigate("/");
  renderApp();
}

// -------------------------------------------------------------
// Home & Auth Views
// -------------------------------------------------------------
function renderHome() {
  return `
    <div style="text-align: center; padding: 40px 16px;">
      <h1 style="font-size: 2.25rem; font-weight: 800; color: #0f172a; margin-bottom: 12px;">
        Theo Dõi Biểu Hiện Da Liễu Bảo Tồn Quyền Riêng Tư
      </h1>
      <p style="font-size: 1.1rem; color: #475569; max-width: 680px; margin: 0 auto 28px;">
        Ghi nhận hình ảnh chuẩn y khoa, đo lường các đặc trưng biến đổi khách quan, đối chiếu kiến thức tham khảo từ Vector DB và chia sẻ hồ sơ an toàn qua Avalanche Blockchain.
      </p>
      <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
        <a href="#/start" class="btn btn-primary" style="padding: 12px 24px; font-size: 1.05rem;">
          Bắt Đầu Tra Cứu & Đánh Giá
        </a>
        <a href="#/register" class="btn btn-outline" style="padding: 12px 24px; font-size: 1.05rem; border-color:#0284c7; color:#0284c7; font-weight:600;">
          📝 Đăng Ký Tài Khoản (Lưu Database)
        </a>
        <a href="#/about-limits" class="btn btn-outline" style="padding: 12px 24px; font-size: 1.05rem;">
          Giới Hạn Hệ Thống (Phụ Lục A)
        </a>
      </div>
    </div>

    <div class="grid-3" style="margin-top: 32px;">
      <div class="card">
        <div style="font-size: 2rem; margin-bottom: 8px;">📷</div>
        <h3 style="margin-bottom: 8px;">Chụp eKYC Chuẩn Khung</h3>
        <p style="color: #64748b; font-size: 0.9rem;">
          Kiểm tra độ nét, ánh sáng và chói lóa tự động. Cắt vùng ROI tổn thương chính xác và hỗ trợ camera trực tiếp.
        </p>
      </div>
      <div class="card">
        <div style="font-size: 2rem; margin-bottom: 8px;">🔬</div>
        <h3 style="margin-bottom: 8px;">Đo Lường & Tra Cứu 64D</h3>
        <p style="color: #64748b; font-size: 0.9rem;">
          Đo 6 đặc trưng ảnh khách quan (diện tích, độ đỏ, độ phân tán, kết cấu...) và tra cứu tương đồng từ 20 bệnh y văn, không chẩn đoán, không tỷ lệ %.
        </p>
      </div>
      <div class="card">
        <div style="font-size: 2rem; margin-bottom: 8px;">⛓️</div>
        <h3 style="margin-bottom: 8px;">Bằng Chứng Avalanche</h3>
        <p style="color: #64748b; font-size: 0.9rem;">
          Ủy quyền xem hồ sơ bằng CSPRNG Nonce bảo vệ danh tính tuyệt đối. Thu hồi quyền tức thì bất kỳ lúc nào.
        </p>
      </div>
    </div>
  `;
}

function renderLogin() {
  return `
    <div class="card" style="max-width: 440px; margin: 40px auto;">
      <h2 style="margin-bottom: 8px; text-align: center;">Đăng Nhập DermaCare</h2>
      <p style="text-align: center; color: #64748b; font-size: 0.875rem; margin-bottom: 20px;">
        Đăng nhập để xem hồ sơ và tiến trình cá nhân
      </p>
      <form onsubmit="window.handleLogin(event)">
        <div class="form-group">
          <label class="form-label">Email:</label>
          <input type="email" class="form-control" id="login-email" required placeholder="name@demo.test">
        </div>
        <div class="form-group">
          <label class="form-label">Mật khẩu:</label>
          <input type="password" class="form-control" id="login-password" required placeholder="••••••••">
        </div>
        <div id="login-error" style="color: #dc2626; font-size: 0.875rem; margin-bottom: 12px; display: none;"></div>
        <button type="submit" class="btn btn-primary" style="width: 100%; margin-bottom: 12px;">Đăng nhập</button>
      </form>
      <div style="text-align: center; margin-top: 12px; font-size: 0.875rem; color: #64748b;">
        Chưa có tài khoản? <a href="#/register" style="color: #0284c7; font-weight: 600;">Đăng ký tài khoản mới</a>
      </div>
      <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 0.8125rem;">
        <p style="color: #64748b; margin-bottom: 8px;">Tài khoản mẫu thử nghiệm (Password123!):</p>
        <div style="display: flex; flex-wrap: wrap; gap: 6px;">
          <button class="btn btn-outline btn-sm" onclick="window.quickLogin('patient@demo.test')">Bệnh nhân</button>
          <button class="btn btn-outline btn-sm" onclick="window.quickLogin('doctor@demo.test')">Bác sĩ</button>
          <button class="btn btn-outline btn-sm" onclick="window.quickLogin('admin@demo.test')">Quản trị</button>
        </div>
      </div>
    </div>
  `;
}

function renderRegister() {
  return `
    <div class="card" style="max-width: 480px; margin: 40px auto;">
      <h2 style="margin-bottom: 8px; text-align: center;">Đăng Ký Tài Khoản Mới</h2>
      <p style="text-align: center; color: #64748b; font-size: 0.875rem; margin-bottom: 20px;">
        Tài khoản được lưu trực tiếp vào cơ sở dữ liệu trên máy tính (SQLite: <code>data/derma.db</code>)
      </p>
      <form onsubmit="window.handleRegister(event)">
        <div class="form-group">
          <label class="form-label">Họ và tên hiển thị:</label>
          <input type="text" class="form-control" id="reg-name" required placeholder="Nguyễn Văn A">
        </div>
        <div class="form-group">
          <label class="form-label">Địa chỉ Email:</label>
          <input type="email" class="form-control" id="reg-email" required placeholder="name@domain.com">
        </div>
        <div class="form-group">
          <label class="form-label">Mật khẩu (tối thiểu 8 ký tự):</label>
          <input type="password" class="form-control" id="reg-password" required minlength="8" placeholder="••••••••">
        </div>
        <div class="form-group">
          <label class="form-label">Xác nhận lại mật khẩu:</label>
          <input type="password" class="form-control" id="reg-confirm-password" required minlength="8" placeholder="••••••••">
        </div>
        <div class="form-group">
          <label class="form-label">Vai trò tài khoản:</label>
          <select class="form-control" id="reg-role">
            <option value="patient">Bệnh nhân / Người dùng cá nhân</option>
            <option value="clinician">Bác sĩ chuyên khoa Da Liễu</option>
          </select>
        </div>
        <div style="margin-bottom: 16px;">
          <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 0.8125rem; color: #475569;">
            <input type="checkbox" id="reg-terms" required checked style="margin-top: 3px;">
            <span>Tôi đồng ý với chính sách bảo mật dữ liệu y tế phi tập trung và cam kết bảo tồn quyền riêng tư.</span>
          </label>
        </div>
        <div id="reg-error" style="color: #dc2626; font-size: 0.875rem; margin-bottom: 12px; display: none;"></div>
        <div id="reg-success" style="color: #16a34a; font-size: 0.875rem; margin-bottom: 12px; display: none;"></div>
        <button type="submit" id="btn-reg-submit" class="btn btn-primary" style="width: 100%; margin-bottom: 14px;">
          Tạo tài khoản & Đăng nhập ngay
        </button>
      </form>
      <div style="text-align: center; border-top: 1px solid #e2e8f0; padding-top: 14px; font-size: 0.875rem; color: #64748b;">
        Đã có tài khoản? <a href="#/login" style="color: #0284c7; font-weight: 600;">Đăng nhập ngay</a>
      </div>
    </div>
  `;
}

window.handleRegister = async (e) => {
  e.preventDefault();
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const confirmPassword = document.getElementById("reg-confirm-password").value;
  const role = document.getElementById("reg-role").value;
  const errDiv = document.getElementById("reg-error");
  const succDiv = document.getElementById("reg-success");
  const btn = document.getElementById("btn-reg-submit");

  errDiv.style.display = "none";
  succDiv.style.display = "none";

  if (password !== confirmPassword) {
    errDiv.innerText = "Mật khẩu xác nhận không khớp.";
    errDiv.style.display = "block";
    return;
  }
  if (password.length < 8) {
    errDiv.innerText = "Mật khẩu phải có ít nhất 8 ký tự.";
    errDiv.style.display = "block";
    return;
  }

  btn.disabled = true;
  btn.innerText = "Đang lưu vào database máy...";

  try {
    const endpoint = role === "clinician" ? "/api/auth/register-clinician" : "/api/auth/register";
    const body = {
      email: email,
      password: password,
      display_name: name,
      clinic_id: role === "clinician" ? "clinic-sg-01" : undefined
    };
    const res = await apiCall(endpoint, "POST", body);

    succDiv.innerText = "Đăng ký thành công! Dữ liệu đã lưu vào database.";
    succDiv.style.display = "block";

    STATE.token = res.access_token;
    STATE.user = res.user;
    localStorage.setItem("dc_token", res.access_token);
    localStorage.setItem("dc_user", JSON.stringify(res.user));

    setTimeout(() => {
      if (res.user.role === "clinician") {
        navigate("/doctor/inbox");
      } else {
        navigate("/cases");
      }
      renderApp();
    }, 600);
  } catch (err) {
    errDiv.innerText = err.message || "Đăng ký thất bại. Vui lòng thử lại.";
    errDiv.style.display = "block";
    btn.disabled = false;
    btn.innerText = "Tạo tài khoản & Đăng nhập ngay";
  }
};

window.quickLogin = (email) => {
  document.getElementById("login-email").value = email;
  document.getElementById("login-password").value = "Password123!";
  document.querySelector("form").dispatchEvent(new Event("submit", { cancelable: true }));
};

window.handleLogin = async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const errDiv = document.getElementById("login-error");
  errDiv.style.display = "none";

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
    renderApp();
  } catch (err) {
    errDiv.innerText = err.message;
    errDiv.style.display = "block";
  }
};

// -------------------------------------------------------------
// Wizard: 6-Step Workflow
// -------------------------------------------------------------
function renderWizard() {
  const step = STATE.wizard.step;
  const stepTitles = [
    "Vị trí da",
    "Triệu chứng",
    "Chụp ảnh",
    "Tham khảo",
    "Phòng khám",
    "Chia sẻ"
  ];

  const stepsHeader = stepTitles.map((title, i) => {
    const sNum = i + 1;
    const isCurrent = (sNum === step);
    const isDone = (sNum < step);
    return `
      <div class="wizard-step ${isCurrent ? 'active' : ''} ${isDone ? 'completed' : ''}">
        <div class="step-circle">${isDone ? '✓' : sNum}</div>
        <div class="step-title">${title}</div>
      </div>
    `;
  }).join("");

  return `
    <div class="card" style="max-width: 840px; margin: 0 auto;">
      <div class="wizard-steps">
        ${stepsHeader}
      </div>
      <div class="wizard-content">
        ${renderWizardStepContent(step)}
      </div>
    </div>
  `;
}

// 28 Symptoms definition (Section 10.2 & intake_general.yaml)
const SYMPTOMS_28_LIST = [
  { id: "itch", label: "Ngứa râm ran hoặc dữ dội" },
  { id: "redness", label: "Vùng da đỏ hoặc hồng sẫm" },
  { id: "scaling", label: "Bong vảy da, tróc vảy trắng" },
  { id: "dryness", label: "Da khô ráp, sần sùi" },
  { id: "oozing", label: "Rỉ dịch vàng hoặc ướt" },
  { id: "crusting", label: "Đóng mày, vảy tiết cứng" },
  { id: "blisters", label: "Mụn nước nhỏ hoặc bọng nước" },
  { id: "pustules", label: "Mụn mủ vàng hoặc trắng" },
  { id: "papules", label: "Nốt sẩn đỏ gồ trên da" },
  { id: "plaques", label: "Mảng da dày nổi gờ rõ" },
  { id: "pain", label: "Cảm giác đau tức hoặc chạm đau" },
  { id: "burning", label: "Cảm giác bỏng rát, châm chích" },
  { id: "bleeding", label: "Chảy máu do nứt nẻ hoặc gãi" },
  { id: "cracking", label: "Nứt nẻ da, kẽ da nứt sâu" },
  { id: "spreading", label: "Tổn thương có xu hướng lan rộng" },
  { id: "recurrent", label: "Từng bị các đợt tương tự trước đây" },
  { id: "ring_shape", label: "Tổn thương hình tròn viền đỏ" },
  { id: "wheals", label: "Mảng sẩn phù mày đay giống muỗi đốt" },
  { id: "pale_patch", label: "Mảng da nhạt màu / mất sắc tố" },
  { id: "dark_patch", label: "Mảng da sẫm màu, sạm nâu" },
  { id: "night_itch_contacts", label: "Ngứa tăng về đêm & người ngủ cùng cũng ngứa" },
  { id: "one_sided_band", label: "Mọc thành dải dồn về một bên cơ thể" },
  { id: "warty_surface", label: "Bề mặt sần sùi giống mụn cóc" },
  { id: "blackheads", label: "Nhân mụn đầu đen hoặc đầu trắng" },
  { id: "contact_trigger", label: "Xuất hiện sau tiếp xúc hoá chất / mỹ phẩm" },
  { id: "flushing", label: "Vùng mặt dễ đỏ bừng từng cơn" },
  { id: "sweat_heat_trigger", label: "Tăng khi trời nóng hoặc ra mồ hôi" },
  { id: "greasy_scale", label: "Vảy nhờn dính màu vàng da đầu/cánh mũi" }
];

// Safety Red Flag questions (15 deterministic safety rules)
const SAFETY_RED_FLAGS = [
  { id: "face_lip_swelling_or_breathing", label: "Sưng phù môi, mặt, mí mắt hoặc cảm thấy khó thở, khó nuốt", urgent: true },
  { id: "fever", label: "Có kèm theo sốt cao hoặc gai rét", urgent: false },
  { id: "spreading_rapidly", label: "Phát ban hoặc vết đỏ lan rất nhanh trong 24–48 giờ qua", urgent: false },
  { id: "blisters_mucosa", label: "Phồng rộp, lở loét ở vùng miệng, mắt hoặc cơ quan sinh dục", urgent: true },
  { id: "skin_peeling_or_raw_large", label: "Da bị tróc từng mảng lớn hoặc trợt loét rỉ dịch diện rộng", urgent: true },
  { id: "purple_nonblanching_spots", label: "Có đốm tím hoặc đen trên da mà khi ấn vào không mờ đi", urgent: false },
  { id: "severe_pain_hot_red_spreading", label: "Vùng da đau dữ dội, sưng đỏ, nóng rát và lan rộng nhanh", urgent: true },
  { id: "red_streak_from_lesion", label: "Có vệt đỏ lan dài ra từ vùng tổn thương", urgent: false },
  { id: "new_medication_recent", label: "Mới bắt đầu uống loại thuốc mới nào trong 2-4 tuần gần đây", urgent: false }
];

function renderWizardStepContent(step) {
  if (step === 1) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 1: Chọn vùng da xuất hiện tổn thương</h3>
        ${ProvenanceBadge("user_reported")}
      </div>
      <p style="color:#64748b; margin-bottom:16px;">Nhấp vào vị trí tương ứng trên hình mô phỏng cơ thể (BodyMap) để xác định vùng giải phẫu.</p>
      ${BodyMap(STATE.wizard.site)}
      <div style="display:flex; justify-content:flex-end; margin-top:24px;">
        <button class="btn btn-primary" onclick="STATE.wizard.step = 2; renderApp();">Tiếp tục: Khai báo triệu chứng →</button>
      </div>
    `;
  } else if (step === 2) {
    const symptomsHtml = SYMPTOMS_28_LIST.map(s => {
      const checked = !!STATE.wizard.symptoms[s.id];
      return `
        <label style="display:flex; align-items:center; gap:8px; font-size:0.875rem; padding:4px 0;">
          <input type="checkbox" id="sym-${s.id}" ${checked ? 'checked' : ''}>
          <span>${s.label}</span>
        </label>
      `;
    }).join("");

    const redFlagsHtml = SAFETY_RED_FLAGS.map(rf => {
      const checked = STATE.wizard.redFlags.includes(rf.id);
      return `
        <label style="display:flex; align-items:center; gap:8px; font-size:0.875rem; margin-bottom:6px; color:#991b1b; font-weight:${rf.urgent ? '600' : 'normal'};">
          <input type="checkbox" id="rf-${rf.id}" ${checked ? 'checked' : ''}>
          <span>${rf.label} ${rf.urgent ? '(Khẩn cấp)' : ''}</span>
        </label>
      `;
    }).join("");

    return `
      <div class="card-header">
        <h3 class="card-title">Bước 2: Khai báo triệu chứng & Dấu hiệu cảnh báo đỏ</h3>
        ${ProvenanceBadge("user_reported")}
      </div>
      <div class="form-group">
        <label class="form-label">Thời gian xuất hiện (Khởi phát):</label>
        <select class="form-control" id="w-onset">
          <option value="onset_lt3d" ${STATE.wizard.onset === 'onset_lt3d' ? 'selected' : ''}>Dưới 3 ngày</option>
          <option value="onset_3_14d" ${(!STATE.wizard.onset || STATE.wizard.onset === 'onset_3_14d') ? 'selected' : ''}>Từ 3 đến 14 ngày</option>
          <option value="onset_2_8w" ${STATE.wizard.onset === 'onset_2_8w' ? 'selected' : ''}>Từ 2 đến 8 tuần</option>
          <option value="onset_gt2m" ${STATE.wizard.onset === 'onset_gt2m' ? 'selected' : ''}>Trên 2 tháng</option>
          <option value="onset_sudden" ${STATE.wizard.onset === 'onset_sudden' ? 'selected' : ''}>Xuất hiện đột ngột chỉ trong vài giờ</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Các biểu hiện ghi nhận (28 đặc trưng tham khảo):</label>
        <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; font-size:0.8125rem; color:#64748b;">
          Đây là trường theo dõi do nhóm thiết kế, KHÔNG phải thang đo đã xác thực.
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; max-height:260px; overflow-y:auto; padding:8px; border:1px solid #e2e8f0; border-radius:6px; background:#fff;">
          ${symptomsHtml}
        </div>
      </div>

      <div class="form-group" style="background:#fef2f2; border:1px solid #fecaca; padding:12px; border-radius:6px;">
        <label class="form-label" style="color:#991b1b; font-weight:700;">⚠️ Dấu hiệu cảnh báo đỏ cần lưu ý:</label>
        <p style="font-size:0.8125rem; color:#7f1d1d; margin-bottom:8px;">Nếu bạn có bất kỳ dấu hiệu nào dưới đây, hệ thống sẽ đề nghị bạn tìm trợ giúp y tế khẩn cấp thay vì tiếp tục đánh giá thông thường.</p>
        <div>
          ${redFlagsHtml}
        </div>
      </div>

      <div id="safety-warning-banner" style="display:none; background:#fee2e2; border:2px solid #ef4444; border-radius:6px; padding:16px; margin-top:16px;">
        <h4 style="color:#991b1b; margin-bottom:8px;">🚨 CẢNH BÁO Y TẾ KHẨN CẤP</h4>
        <div id="safety-warning-text" style="color:#7f1d1d; font-size:0.9rem; line-height:1.5;"></div>
        <div style="margin-top:12px;">
          <a href="tel:115" class="btn btn-danger" style="display:inline-block; margin-right:8px;">📞 Gọi Tổng Đài Cấp Cứu 115</a>
        </div>
      </div>

      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 1; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" id="btn-save-symptoms" onclick="window.saveWizardSymptoms()">Tiếp tục: Chụp ảnh tổn thương →</button>
      </div>
    `;
  } else if (step === 3) {
    const hasImage = !!STATE.wizard.previewSrc;
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 3: Chụp ảnh tổn thương với khung kiểm tra chất lượng</h3>
        ${ProvenanceBadge("ai_measured")}
      </div>
      <p style="color:#64748b; margin-bottom:12px;">Đảm bảo camera cách tổn thương 15-20cm, ánh sáng tự nhiên đều, không bị bóng mờ hay chói sáng.</p>
      
      <div class="capture-box" id="capture-container">
        <!-- Tùy chọn 1: Menu lựa chọn song song (Camera hoặc Thư viện hoặc Ảnh mẫu) -->
        <div id="capture-placeholder" style="${hasImage ? 'display:none;' : 'display:block;'}">
          <div style="font-size:3rem; margin-bottom:8px;">📸</div>
          <p style="margin-bottom:14px; font-weight:500; color:#1e293b;">
            Chụp trực tiếp từ camera hoặc chọn ảnh từ thư viện thiết bị
          </p>
          <input type="file" id="image-input" accept="image/*" style="display:none;" onchange="window.handleImageSelect(event)">
          <div class="capture-options">
            <button type="button" class="btn btn-primary" onclick="window.startCameraStream()">
              📷 Mở camera chụp trực tiếp
            </button>
            <button type="button" class="btn btn-outline" onclick="document.getElementById('image-input').click()">
              🖼️ Chọn ảnh từ thư viện
            </button>
            <button type="button" class="btn btn-outline btn-sm" onclick="window.useSampleImage()">
              🧪 Sử dụng ảnh mẫu sắc nét
            </button>
          </div>
        </div>

        <!-- Tùy chọn 2: Khung hình Camera trực tiếp -->
        <div id="camera-view" style="display:none; width:100%;">
          <div class="camera-feed-container">
            <video id="camera-video" class="camera-video" autoplay playsinline muted></video>
            <div class="camera-reticle">
              <div class="camera-reticle-inner"></div>
            </div>
            <div class="camera-reticle-text">Căn chỉnh vùng tổn thương vào giữa khung (15–20cm)</div>
          </div>
          <div class="camera-controls-bar">
            <button type="button" class="btn btn-outline btn-sm" style="color:#ffffff; border-color:#475569;" onclick="window.switchCamera()" title="Đổi camera trước/sau">
              🔄 Đổi camera
            </button>
            <button type="button" class="btn-shutter" onclick="window.captureSnapshot()" title="Bấm chụp ảnh">
              📸
            </button>
            <button type="button" class="btn btn-outline btn-sm" style="color:#ffffff; border-color:#475569;" onclick="window.stopCameraStream()" title="Đóng camera">
              ✕ Đóng
            </button>
          </div>
        </div>

        <!-- Tùy chọn 3: Xem trước ảnh đã chụp / chọn -->
        <div id="capture-preview-container" style="${hasImage ? 'display:block;' : 'display:none;'} width:100%;">
          <img id="capture-preview" class="capture-preview-img" src="${STATE.wizard.previewSrc || ''}" />
          <div class="preview-actions-bar">
            <button type="button" class="btn btn-primary btn-sm" onclick="window.startCameraStream()">
              📷 Chụp lại bằng camera
            </button>
            <button type="button" class="btn btn-outline btn-sm" onclick="document.getElementById('image-input').click()">
              🖼️ Chọn ảnh khác từ thư viện
            </button>
            <button type="button" class="btn btn-outline btn-sm" onclick="window.useSampleImage()">
              🧪 Dùng ảnh mẫu
            </button>
          </div>
        </div>

        <canvas id="capture-canvas" style="display:none;"></canvas>
      </div>

      <div id="quality-card-area">
        ${QualityResultCard(STATE.wizard.qualityResult)}
        ${STATE.wizard.measurements && STATE.wizard.measurements.length > 0 ? `
          <div class="card" style="margin-top:12px; background:#f8fafc; border:1px solid #e2e8f0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <strong>Số đo đặc trưng hình thái học tổn thương:</strong>
              ${ProvenanceBadge("ai_measured")}
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:0.875rem;">
              ${STATE.wizard.measurements.filter(m => m.metric_name !== 'lesion_count' && m.metric_name !== 'measurement_status').map(m => `
                <div>• ${m.metric_name}: <strong>${Number(m.value).toFixed(2)} ${m.unit || ''}</strong></div>
              `).join("")}
            </div>
          </div>
        ` : ''}
      </div>

      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="window.stopCameraStream(); STATE.wizard.step = 2; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" id="btn-to-step-4" ${(STATE.wizard.qualityResult?.status === 'PASS' || STATE.wizard.qualityResult?.status === 'REVIEW') ? '' : 'disabled'} onclick="window.stopCameraStream(); STATE.wizard.step = 4; renderApp();">Tiếp tục: Xem danh sách tham khảo →</button>
      </div>
    `;
  } else if (step === 4) {
    const conditions = STATE.wizard.similarConditions?.items || STATE.wizard.similarConditions || [];
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 4: Tình trạng có biểu hiện lâm sàng tương đồng</h3>
        ${ProvenanceBadge("ai_measured")}
      </div>
      ${SimilarConditionsPanel(conditions)}
      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 3; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" onclick="STATE.wizard.step = 5; renderApp();">Tiếp tục: Tìm cơ sở y tế chuyên khoa gần nhất →</button>
      </div>
    `;
  } else if (step === 5) {
    return `
      <div class="card-header">
        <h3 class="card-title">Bước 5: Tìm kiếm cơ sở y tế chuyên khoa Da Liễu gần bạn</h3>
        ${ProvenanceBadge("user_reported")}
      </div>
      <p style="color:#64748b; margin-bottom:12px;">Toạ độ GPS của bạn chỉ dùng để tính khoảng cách tạm thời và KHÔNG lưu trữ trên máy chủ.</p>
      
      <!-- Live GPS Device Status Banner -->
      <div id="gps-status-indicator" style="margin-bottom: 14px; padding: 10px 14px; border-radius: 8px; background: #f0fdf4; border: 1px solid #86efac; font-size: 0.875rem; color: #166534; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <span>📡 Đang đồng bộ vị trí theo cảm biến GPS thiết bị của bạn...</span>
        <button class="btn btn-outline btn-sm" style="padding: 3px 8px; font-size: 0.75rem;" onclick="window.getUserLocation(true)">📍 Cập nhật vị trí</button>
      </div>

      <div style="display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap;">
        <button class="btn btn-primary btn-sm" onclick="window.getUserLocation(true)">📍 Định vị lại GPS thiết bị</button>
        <span style="font-size:0.8125rem; color:#64748b;">Hoặc chọn nhanh khu vực:</span>
        <select class="form-control" style="width:auto; padding:4px 8px; font-size:0.8125rem;" onchange="window.selectFallbackLocation(this.value)">
          <option value="current">📍 Vị trí thiết bị hiện tại</option>
          <option value="10.7769,106.7009">TP. Hồ Chí Minh (Quận 1)</option>
          <option value="10.7554,106.6667">TP. Hồ Chí Minh (Quận 5)</option>
          <option value="10.7303,106.7218">TP. Hồ Chí Minh (Quận 7)</option>
          <option value="10.8512,106.7719">TP. Thủ Đức</option>
          <option value="21.0285,105.8542">Hà Nội (Hoàn Kiếm)</option>
          <option value="16.0544,108.2022">Đà Nẵng (Hải Châu)</option>
          <option value="10.0452,105.7469">Cần Thơ (Ninh Kiều)</option>
        </select>
      </div>

      <div id="clinics-leaflet-map" style="height:320px; width:100%; border-radius:8px; border:1px solid #cbd5e1; margin-bottom:16px; background:#f1f5f9;"></div>

      <div id="clinics-list-area">
        <p style="color:#64748b;">Đang tìm kiếm các cơ sở y tế chuyên khoa...</p>
      </div>

      <div style="display:flex; justify-content:space-between; margin-top:24px;">
        <button class="btn btn-outline" onclick="STATE.wizard.step = 4; renderApp();">← Quay lại</button>
        <button class="btn btn-primary" onclick="STATE.wizard.step = 6; renderApp();">Tiếp tục: Thiết lập chia sẻ hồ sơ →</button>
      </div>
    `;
  } else if (step === 6) {
    const clinicName = STATE.wizard.selectedClinic?.name || "Phòng khám Da liễu Sài Gòn (Verified Partner)";
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
        <input type="text" class="form-control" value="${clinicName}" readonly>
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

// -------------------------------------------------------------
// Step 2: Symptoms & Safety Check
// -------------------------------------------------------------
window.saveWizardSymptoms = async () => {
  const onset = document.getElementById("w-onset").value;
  STATE.wizard.onset = onset;

  const symptoms = {};
  SYMPTOMS_28_LIST.forEach(s => {
    const el = document.getElementById(`sym-${s.id}`);
    if (el && el.checked) {
      symptoms[s.id] = "many";
    }
  });
  STATE.wizard.symptoms = symptoms;

  const redFlags = [];
  SAFETY_RED_FLAGS.forEach(rf => {
    const el = document.getElementById(`rf-${rf.id}`);
    if (el && el.checked) {
      redFlags.push(rf.id);
      symptoms[rf.id] = true;
    }
  });
  STATE.wizard.redFlags = redFlags;

  const btn = document.getElementById("btn-save-symptoms");
  if (btn) btn.innerText = "Đang kiểm tra an toàn...";

  try {
    const safetyRes = await apiCall("/api/safety/check", "POST", {
      symptoms,
      profile_type: STATE.wizard.profileType || "other"
    });

    if (safetyRes.is_urgent) {
      const banner = document.getElementById("safety-warning-banner");
      const textDiv = document.getElementById("safety-warning-text");
      if (banner && textDiv) {
        textDiv.innerHTML = `
          <p style="margin-bottom:8px;">Các dấu hiệu bạn khai báo có tính chất cấp thiết y khoa:</p>
          <ul style="margin-left:20px; margin-bottom:12px;">
            ${(safetyRes.messages || []).map(m => `<li><strong>${m}</strong></li>`).join("")}
          </ul>
          <p>DermaCare Agent dừng quy trình đánh giá vì an toàn sức khỏe của bạn. Vui lòng đến ngay cơ sở y tế hoặc khoa cấp cứu gần nhất!</p>
        `;
        banner.style.display = "block";
        if (btn) {
          btn.setAttribute("disabled", "disabled");
          btn.innerText = "Dừng quy trình đánh giá";
        }
      }
      return;
    }
  } catch (err) {
    console.warn("Safety check network warning:", err);
  }

  STATE.wizard.step = 3;
  renderApp();
};

// -------------------------------------------------------------
// Step 3: Camera Capture & Live Analysis
// -------------------------------------------------------------
let currentCameraStream = null;
let currentFacingMode = "environment";

window.startCameraStream = async () => {
  const placeholder = document.getElementById("capture-placeholder");
  const cameraView = document.getElementById("camera-view");
  const previewContainer = document.getElementById("capture-preview-container");
  const video = document.getElementById("camera-video");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Trình duyệt không hỗ trợ camera. Vui lòng chọn ảnh từ thư viện.");
    return;
  }

  if (currentCameraStream) {
    try {
      currentCameraStream.getTracks().forEach(t => t.stop());
    } catch (_) {}
    currentCameraStream = null;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: currentFacingMode,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    });
    currentCameraStream = stream;
    if (placeholder) placeholder.style.display = "none";
    if (previewContainer) previewContainer.style.display = "none";
    if (cameraView) cameraView.style.display = "block";
    if (video) {
      video.srcObject = stream;
      try { await video.play(); } catch (_) {}
    }
  } catch (err) {
    console.warn("Camera with ideal constraints failed, trying fallback:", err);
    try {
      const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      currentCameraStream = fallbackStream;
      if (placeholder) placeholder.style.display = "none";
      if (previewContainer) previewContainer.style.display = "none";
      if (cameraView) cameraView.style.display = "block";
      if (video) {
        video.srcObject = fallbackStream;
        try { await video.play(); } catch (_) {}
      }
    } catch (fallbackErr) {
      alert("Không thể mở camera. Vui lòng cấp quyền truy cập camera trong trình duyệt hoặc sử dụng tùy chọn Chọn ảnh từ thư viện.");
    }
  }
};

window.stopCameraStream = () => {
  if (currentCameraStream) {
    try {
      currentCameraStream.getTracks().forEach(t => t.stop());
    } catch (_) {}
    currentCameraStream = null;
  }
  const video = document.getElementById("camera-video");
  if (video) video.srcObject = null;

  const placeholder = document.getElementById("capture-placeholder");
  const cameraView = document.getElementById("camera-view");
  const previewContainer = document.getElementById("capture-preview-container");

  if (cameraView) cameraView.style.display = "none";
  if (STATE.wizard.previewSrc) {
    if (previewContainer) previewContainer.style.display = "block";
  } else {
    if (placeholder) placeholder.style.display = "block";
  }
};

window.switchCamera = async () => {
  currentFacingMode = (currentFacingMode === "environment") ? "user" : "environment";
  await window.startCameraStream();
};

window.captureSnapshot = () => {
  const video = document.getElementById("camera-video");
  if (!video || !video.videoWidth) {
    alert("Camera chưa sẵn sàng. Vui lòng đợi trong giây lát.");
    return;
  }

  let canvas = document.getElementById("capture-canvas");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.id = "capture-canvas";
    canvas.style.display = "none";
    document.body.appendChild(canvas);
  }

  // Max dimension 1280px client-side resize
  const maxDim = 1280;
  let w = video.videoWidth;
  let h = video.videoHeight;
  if (Math.max(w, h) > maxDim) {
    const scale = maxDim / Math.max(w, h);
    w = Math.round(w * scale);
    h = Math.round(h * scale);
  }

  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, w, h);

  const dataUrl = canvas.toDataURL("image/jpeg", 0.90);
  STATE.wizard.previewSrc = dataUrl;

  window.stopCameraStream();

  const previewContainer = document.getElementById("capture-preview-container");
  const previewImg = document.getElementById("capture-preview");
  const placeholder = document.getElementById("capture-placeholder");

  if (placeholder) placeholder.style.display = "none";
  if (previewContainer) previewContainer.style.display = "block";
  if (previewImg) previewImg.src = dataUrl;

  window.analyzeWizardImage(dataUrl);
};

window.handleImageSelect = (e) => {
  const file = e.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (evt) => {
    const rawDataUrl = evt.target.result;
    const img = new Image();
    img.onload = () => {
      let canvas = document.getElementById("capture-canvas");
      if (!canvas) {
        canvas = document.createElement("canvas");
        canvas.id = "capture-canvas";
        canvas.style.display = "none";
        document.body.appendChild(canvas);
      }

      const maxDim = 1280;
      let w = img.width;
      let h = img.height;
      if (Math.max(w, h) > maxDim) {
        const scale = maxDim / Math.max(w, h);
        w = Math.round(w * scale);
        h = Math.round(h * scale);
      }
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, w, h);

      const optimizedDataUrl = canvas.toDataURL("image/jpeg", 0.90);
      STATE.wizard.previewSrc = optimizedDataUrl;

      const placeholder = document.getElementById("capture-placeholder");
      const previewContainer = document.getElementById("capture-preview-container");
      const previewImg = document.getElementById("capture-preview");

      if (placeholder) placeholder.style.display = "none";
      if (previewContainer) previewContainer.style.display = "block";
      if (previewImg) previewImg.src = optimizedDataUrl;

      window.analyzeWizardImage(optimizedDataUrl);
    };
    img.src = rawDataUrl;
  };
  reader.readAsDataURL(file);
};

// Client-side precheck function
window.evaluateImageQuality = (canvas, ctx) => {
  const w = canvas.width;
  const h = canvas.height;
  const sampleW = Math.min(240, w);
  const sampleH = Math.min(240, h);
  const startX = Math.floor((w - sampleW) / 2);
  const startY = Math.floor((h - sampleH) / 2);

  const imgData = ctx.getImageData(startX, startY, sampleW, sampleH);
  const data = imgData.data;
  const pixelCount = sampleW * sampleH;

  let totalLum = 0;
  let glareCount = 0;
  const gray = new Float32Array(pixelCount);

  for (let i = 0; i < pixelCount; i++) {
    const idx = i * 4;
    const lum = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];
    gray[i] = lum;
    totalLum += lum;
    if (data[idx] > 248 && data[idx + 1] > 248 && data[idx + 2] > 248) {
      glareCount++;
    }
  }

  const avgExposure = totalLum / pixelCount;
  const glareRatio = glareCount / pixelCount;

  let lapSum = 0;
  let lapSumSq = 0;
  let count = 0;
  for (let y = 1; y < sampleH - 1; y++) {
    for (let x = 1; x < sampleW - 1; x++) {
      const c = gray[y * sampleW + x];
      const top = gray[(y - 1) * sampleW + x];
      const bottom = gray[(y + 1) * sampleW + x];
      const left = gray[y * sampleW + (x - 1)];
      const right = gray[y * sampleW + (x + 1)];
      const lap = 4 * c - (top + bottom + left + right);
      lapSum += lap;
      lapSumSq += lap * lap;
      count++;
    }
  }

  const meanLap = count > 0 ? (lapSum / count) : 0;
  const variance = count > 0 ? (lapSumSq / count) - (meanLap * meanLap) : 0;
  const sharpness = Math.max(0, variance);

  return {
    status: (sharpness >= 45 && avgExposure >= 45 && avgExposure <= 220 && glareRatio < 0.15) ? "PASS" : "REVIEW",
    sharpness_score: Number(sharpness.toFixed(1)),
    exposure_score: Number(avgExposure.toFixed(1)),
    glare_ratio: Number(glareRatio.toFixed(3)),
    resolution: [w, h]
  };
};

window.analyzeWizardImage = async (dataUrl) => {
  const qArea = document.getElementById("quality-card-area");
  if (qArea) {
    qArea.innerHTML = `
      <div class="card" style="text-align:center; padding:24px;">
        <div style="font-size:1.5rem; margin-bottom:8px;">⏳</div>
        <p style="color:#0284c7; font-weight:600;">AI đang đánh giá chất lượng ảnh và tra cứu cơ sở kiến thức...</p>
      </div>
    `;
  }

  try {
    const payload = {
      image_base64: dataUrl,
      body_site: STATE.wizard.site || "face",
      profile_type: STATE.wizard.profileType || "other",
      symptoms: STATE.wizard.symptoms || {},
      onset: STATE.wizard.onset || "onset_3_14d"
    };

    const res = await apiCall("/api/wizard/analyze", "POST", payload);

    STATE.wizard.qualityResult = res.quality;
    STATE.wizard.measurements = res.measurements || [];
    STATE.wizard.similarConditions = res.similar_conditions || { items: [] };
    if (res.case_id) STATE.wizard.caseId = res.case_id;
    if (res.observation_id) STATE.wizard.observationId = res.observation_id;

    const isPass = res.quality.status === "PASS" || res.quality.status === "REVIEW";

    if (qArea) {
      qArea.innerHTML = `
        ${QualityResultCard(res.quality)}
        ${STATE.wizard.measurements && STATE.wizard.measurements.length > 0 ? `
          <div class="card" style="margin-top:12px; background:#f8fafc; border:1px solid #e2e8f0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <strong>Số đo đặc trưng hình thái học tổn thương:</strong>
              ${ProvenanceBadge("ai_measured")}
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:0.875rem;">
              ${STATE.wizard.measurements.filter(m => m.metric_name !== 'lesion_count' && m.metric_name !== 'measurement_status').map(m => `
                <div>• ${m.metric_name}: <strong>${Number(m.value).toFixed(2)} ${m.unit || ''}</strong></div>
              `).join("")}
            </div>
          </div>
        ` : ''}
      `;
    }

    const btnNext = document.getElementById("btn-to-step-4");
    if (btnNext) {
      if (isPass) {
        btnNext.removeAttribute("disabled");
      } else {
        btnNext.setAttribute("disabled", "disabled");
      }
    }
  } catch (err) {
    if (qArea) {
      qArea.innerHTML = `
        <div class="card" style="border-color:#fca5a5; background:#fef2f2;">
          <p style="color:#dc2626;">Lỗi phân tích: ${err.message}</p>
        </div>
      `;
    }
  }
};

window.useSampleImage = async () => {
  window.stopCameraStream();

  // Create a synthetic skin lesion sample via canvas
  let canvas = document.getElementById("capture-canvas");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.id = "capture-canvas";
    canvas.style.display = "none";
    document.body.appendChild(canvas);
  }
  canvas.width = 640;
  canvas.height = 480;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#f5d0b5";
  ctx.fillRect(0, 0, 640, 480);
  ctx.fillStyle = "#d9534f";
  ctx.beginPath();
  ctx.arc(320, 240, 60, 0, Math.PI * 2);
  ctx.fill();

  const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
  STATE.wizard.previewSrc = dataUrl;

  const placeholder = document.getElementById("capture-placeholder");
  const cameraView = document.getElementById("camera-view");
  const previewContainer = document.getElementById("capture-preview-container");
  const previewImg = document.getElementById("capture-preview");

  if (placeholder) placeholder.style.display = "none";
  if (cameraView) cameraView.style.display = "none";
  if (previewContainer) previewContainer.style.display = "block";
  if (previewImg) previewImg.src = dataUrl;

  await window.analyzeWizardImage(dataUrl);
};

// -------------------------------------------------------------
// Step 5: Clinics Map & Selection
// -------------------------------------------------------------
let leafletMapInstance = null;

window.selectFallbackLocation = (val) => {
  if (val === "current") {
    window.getUserLocation(true);
  } else {
    const [lat, lng] = val.split(",").map(Number);
    const statusEl = document.getElementById("gps-status-indicator");
    if (statusEl) {
      statusEl.innerHTML = `
        <span>📍 <strong>Đang định vị theo khu vực chọn:</strong> (${lat.toFixed(4)}, ${lng.toFixed(4)})</span>
        <button class="btn btn-outline btn-sm" style="padding:2px 8px; font-size:0.75rem;" onclick="window.getUserLocation(true)">Dùng GPS thiết bị</button>
      `;
      statusEl.style.background = "#eff6ff";
      statusEl.style.borderColor = "#93c5fd";
      statusEl.style.color = "#1e40af";
    }
    window.loadClinicsMap(lat, lng, false);
  }
};

window.getUserLocation = (force = false) => {
  const statusEl = document.getElementById("gps-status-indicator");
  if (STATE.deviceGps && !force) {
    const { lat, lng, acc } = STATE.deviceGps;
    if (statusEl) {
      statusEl.innerHTML = `
        <span>🟢 <strong>Vị trí thiết bị:</strong> ${lat.toFixed(4)}, ${lng.toFixed(4)} (độ chính xác ~${acc}m). Khoảng cách tính trực tiếp từ thiết bị của bạn.</span>
        <button class="btn btn-outline btn-sm" style="padding:2px 8px; font-size:0.75rem;" onclick="window.getUserLocation(true)">🔄 Cập nhật lại</button>
      `;
      statusEl.style.background = "#f0fdf4";
      statusEl.style.borderColor = "#86efac";
      statusEl.style.color = "#166534";
    }
    window.loadClinicsMap(lat, lng, true);
    return;
  }

  if (statusEl) {
    statusEl.innerHTML = `<span>📡 Đang kết nối cảm biến GPS thiết bị để lấy toạ độ thực tế...</span>`;
    statusEl.style.background = "#f0fdf4";
  }

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const acc = Math.round(pos.coords.accuracy || 10);
        STATE.deviceGps = { lat, lng, acc };
        if (statusEl) {
          statusEl.innerHTML = `
            <span>🟢 <strong>Đã cập nhật vị trí thiết bị:</strong> ${lat.toFixed(4)}, ${lng.toFixed(4)} (độ chính xác ~${acc}m). Khoảng cách phòng khám được tính theo thiết bị của bạn.</span>
            <button class="btn btn-outline btn-sm" style="padding:2px 8px; font-size:0.75rem;" onclick="window.getUserLocation(true)">🔄 Cập nhật lại</button>
          `;
          statusEl.style.background = "#f0fdf4";
          statusEl.style.borderColor = "#86efac";
          statusEl.style.color = "#166534";
        }
        window.loadClinicsMap(lat, lng, true);
      },
      (err) => {
        let msg = "Không thể lấy toạ độ GPS thiết bị (chưa cấp quyền hoặc trình duyệt hạn chế HTTP).";
        if (err.code === 1) msg = "Quyền truy cập vị trí bị từ chối trên thiết bị/trình duyệt.";
        if (statusEl) {
          statusEl.innerHTML = `
            <span>⚠️ ${msg} Đang dùng toạ độ trung tâm TP.HCM làm mốc. Bạn có thể chọn khu vực trong danh sách.</span>
            <button class="btn btn-outline btn-sm" style="padding:2px 8px; font-size:0.75rem;" onclick="window.getUserLocation(true)">Thử lại</button>
          `;
          statusEl.style.background = "#fefce8";
          statusEl.style.borderColor = "#fef08a";
          statusEl.style.color = "#854d0e";
        }
        window.loadClinicsMap(10.7769, 106.7009, false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  } else {
    window.loadClinicsMap(10.7769, 106.7009, false);
  }
};

window.loadClinicsMap = async (lat = 10.7769, lng = 106.7009, isDevice = false) => {
  const mapContainer = document.getElementById("clinics-leaflet-map");
  const listArea = document.getElementById("clinics-list-area");

  if (!mapContainer || !listArea) return;

  try {
    const list = await apiCall(`/api/clinics/nearby?lat=${lat}&lng=${lng}&radius_km=30`);
    listArea.innerHTML = list.map(c => ClinicCard(c)).join("");

    if (window.L) {
      if (leafletMapInstance) {
        leafletMapInstance.remove();
        leafletMapInstance = null;
      }
      leafletMapInstance = L.map(mapContainer).setView([lat, lng], 13);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap"
      }).addTo(leafletMapInstance);

      // Distinct Blue Pin for User/Device
      const userIcon = L.divIcon({
        className: 'user-gps-marker',
        html: `<div style="background:#0284c7; color:#fff; padding:4px 8px; border-radius:16px; font-size:11px; font-weight:700; box-shadow:0 2px 8px rgba(0,0,0,0.3); border:2px solid #fff; white-space:nowrap;">📍 ${isDevice ? 'Vị trí thiết bị của bạn' : 'Vị trí tìm kiếm'}</div>`,
        iconSize: [140, 26],
        iconAnchor: [70, 13]
      });
      L.marker([lat, lng], { icon: userIcon }).addTo(leafletMapInstance).bindPopup(`<strong>${isDevice ? 'Vị trí thiết bị của bạn' : 'Vị trí tìm kiếm'}</strong><br>Vĩ độ: ${lat.toFixed(4)}, Kinh độ: ${lng.toFixed(4)}`).openPopup();

      // Markers for clinics
      list.forEach(c => {
        if (c.lat && c.lng) {
          const marker = L.marker([c.lat, c.lng]).addTo(leafletMapInstance);
          const partnerBadge = c.is_partner ? '<span style="color:#16a34a; font-weight:bold;">★ VERIFIED PARTNER</span><br>' : '';
          const distStr = c.distance_km !== undefined ? `<br>Khoảng cách: <strong>${c.distance_km.toFixed(1)} km</strong>` : '';
          marker.bindPopup(`<strong>${c.name}</strong><br>${partnerBadge}${c.address_text || ''}${distStr}`);
        }
      });
    }
  } catch (err) {
    listArea.innerHTML = `<p style="color:#dc2626;">Không thể tải danh sách phòng khám: ${err.message}</p>`;
  }
};

window.selectClinicForConsent = (clinicId) => {
  STATE.wizard.selectedClinic = { id: clinicId, name: "Phòng khám Da liễu Sài Gòn (Verified Partner)" };
  STATE.wizard.step = 6;
  renderApp();
};

// -------------------------------------------------------------
// Step 6: Finalize Wizard (Blockchain Avalanche Consent)
// -------------------------------------------------------------
window.finalizeWizard = async () => {
  if (!STATE.token) {
    alert("Vui lòng đăng nhập tài khoản để lưu hồ sơ và kích hoạt ủy quyền chia sẻ.");
    navigate("/login");
    return;
  }

  const scopeVal = document.getElementById("consent-scope")?.value || "full";
  const daysVal = parseInt(document.getElementById("consent-expiry")?.value || "30", 10);
  const clinicId = STATE.wizard.selectedClinic?.id || "clinic-sg-01";

  try {
    let caseId = STATE.wizard.caseId;
    if (!caseId) {
      const caseRes = await apiCall("/api/cases", "POST", {
        body_site: STATE.wizard.site || "face",
        profile_type: STATE.wizard.profileType || "other"
      });
      caseId = caseRes.id;
      STATE.wizard.caseId = caseId;
    }

    // Save symptoms
    await apiCall(`/api/cases/${caseId}/symptoms`, "POST", {
      answers: STATE.wizard.symptoms || {},
      onset: STATE.wizard.onset || "onset_3_14d"
    }).catch(() => {});

    // Create consent on chain
    const consentRes = await apiCall("/api/consents", "POST", {
      case_id: caseId,
      recipient_clinic_id: clinicId,
      scope: {
        images: scopeVal === "full",
        measurements: true,
        symptoms: true,
        reports: true
      },
      days: daysVal
    });

    alert(`Xác lập ủy quyền thành công!\nTxHash Avalanche: ${consentRes.tx_hash}\nCam kết không PII: ${consentRes.commitment.slice(0, 16)}...`);
    navigate(`/cases/${caseId}`);
  } catch (err) {
    alert(`Lỗi xác lập ủy quyền: ${err.message}`);
  }
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
    const caseList = await apiCall("/api/cases");
    const area = document.getElementById("cases-content");
    if (!caseList || caseList.length === 0) {
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
        ${caseList.map(cs => `
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">${cs.title || 'Hồ sơ vùng ' + (cs.body_site || 'da')}</h3>
              <span class="badge-provenance badge-user">${cs.profile_type}</span>
            </div>
            <p style="color:#64748b; font-size:0.875rem;">Vị trí giải phẫu: <strong>${cs.body_site}</strong></p>
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
    <div id="case-detail-content">
      <p style="color:#64748b;">Đang tải chi tiết hồ sơ...</p>
    </div>
  `;

  try {
    const cs = await apiCall(`/api/cases/${caseId}`);
    const area = document.getElementById("case-detail-content");
    area.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Hồ Sơ: ${cs.body_site || 'Da liễu'}</h3>
          <span class="badge-provenance badge-user">${cs.profile_type || 'other'}</span>
        </div>
        <p style="color:#64748b; font-size:0.875rem;">Mã hồ sơ: <code>${cs.id}</code> | Khởi tạo: ${cs.created_at ? cs.created_at.replace('T', ' ').slice(0, 19) : ''}</p>
        <p style="font-size:0.875rem; margin-top:6px;">Trạng thái hồ sơ: <strong>${cs.status || 'active'}</strong></p>

        <div style="margin:24px 0;">
          <h4 style="margin-bottom:12px;">Các mốc quan sát (Observations):</h4>
          ${cs.observations && cs.observations.length > 0 ? cs.observations.map((obs, idx) => `
            <div class="card" style="background:#fafafa; border:1px solid #e2e8f0; margin-bottom:10px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>Mốc ${idx + 1}: ${obs.captured_at ? obs.captured_at.replace('T', ' ').slice(0, 19) : ''}</strong>
                ${ProvenanceBadge("ai_measured")}
              </div>
              <p style="font-size:0.875rem; color:#64748b; margin-top:4px;">
                Trạng thái: <strong>${obs.workflow_state || 'ANALYZED'}</strong>
              </p>
            </div>
          `).join("") : '<p style="color:#64748b; font-style:italic;">Chưa có mốc chụp bổ sung.</p>'}
        </div>

        <div style="display:flex; gap:12px;">
          <a href="#/cases/${caseId}/timeline" class="btn btn-outline">Xem biểu đồ chuỗi thời gian</a>
          <a href="#/cases/${caseId}/report" class="btn btn-primary">Xuất báo cáo PDF</a>
        </div>
      </div>
    `;
  } catch (err) {
    document.getElementById("case-detail-content").innerHTML = `
      <div class="card"><p style="color:#dc2626;">Lỗi tải hồ sơ: ${err.message}</p></div>
    `;
  }
}

async function renderTimelineView(root, caseId) {
  root.innerHTML = `
    <div style="margin-bottom:16px;">
      <a href="#/cases/${caseId}" class="btn btn-outline btn-sm">← Chi tiết hồ sơ</a>
    </div>
    <div id="timeline-content">
      <p style="color:#64748b;">Đang tải dữ liệu chuỗi thời gian...</p>
    </div>
  `;

  try {
    const tl = await apiCall(`/api/cases/${caseId}/timeline?metric=affected_area_ratio`);
    const area = document.getElementById("timeline-content");
    const points = tl.points || [];

    area.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Chuỗi Thời Gian & Xu Hướng Tiến Triển</h3>
          ${ComparabilityBadge(points.length >= 2 ? "COMPARABLE" : "PARTIAL")}
        </div>
        <p style="color:#64748b; font-size:0.875rem; margin-bottom:16px;">
          Chỉ số định lượng được đo từ các bức ảnh đạt chuẩn chất lượng cùng vị trí giải phẫu.
        </p>

        ${tl.can_draw_trend ? MetricChart(points, "Diện tích tổn thương ước lượng", "%") : `
          <div class="card" style="text-align:center; padding:32px 16px; background:#fafafa;">
            <p style="color:#64748b;">${tl.trend_summary || 'Chưa đủ 3 mốc quan sát đạt tiêu chuẩn để vẽ đường xu hướng.'}</p>
          </div>
        `}

        <div style="margin-top:20px; padding:12px; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0; font-size:0.8125rem; color:#475569;">
          <strong>Quy tắc so sánh (Mục 11):</strong> Nếu hình ảnh chụp khác góc chụp hoặc khác điều kiện ánh sáng vượt ngưỡng cho phép, hệ thống sẽ gắn nhãn <em>Không thể so sánh</em> và ngừng tính toán độ chênh lệch để đảm bảo tính an toàn y học.
        </div>
      </div>
    `;
  } catch (err) {
    document.getElementById("timeline-content").innerHTML = `
      <div class="card"><p style="color:#dc2626;">Lỗi tải biểu đồ: ${err.message}</p></div>
    `;
  }
}

async function renderReportView(root, caseId) {
  root.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;" class="no-print">
      <a href="#/cases/${caseId}" class="btn btn-outline btn-sm">← Quay lại</a>
      <div id="report-actions-bar">
        <button class="btn btn-outline btn-sm" onclick="window.print()">In trang này</button>
      </div>
    </div>
    <div id="report-view-container">
      <p style="color:#64748b;">Đang tạo báo cáo y khoa...</p>
    </div>
  `;

  try {
    const repRes = await apiCall(`/api/cases/${caseId}/reports`, "POST", { audience: "patient" });
    const repId = repRes.report_id;
    const rep = await apiCall(`/api/reports/${repId}`);

    const actionsBar = document.getElementById("report-actions-bar");
    if (actionsBar) {
      actionsBar.innerHTML = `
        <a href="/api/reports/${repId}/pdf" target="_blank" class="btn btn-primary btn-sm">📥 Tải báo cáo PDF chuẩn</a>
        <button class="btn btn-outline btn-sm" onclick="window.print()">In</button>
      `;
    }

    const container = document.getElementById("report-view-container");
    if (container && rep.content && rep.content.html_content) {
      container.innerHTML = `
        <div class="card" style="padding:24px; background:#fff;">
          ${rep.content.html_content}
        </div>
      `;
    }
  } catch (err) {
    document.getElementById("report-view-container").innerHTML = `
      <div class="card"><p style="color:#dc2626;">Không thể tải báo cáo: ${err.message}</p></div>
    `;
  }
}

// -------------------------------------------------------------
// Sharing & Consents View
// -------------------------------------------------------------
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
      <p style="color:#64748b;">Đang tải danh sách ủy quyền...</p>
    </div>
  `;

  try {
    const list = await apiCall("/api/consents");
    const area = document.getElementById("sharing-consents-list");
    if (!list || list.length === 0) {
      area.innerHTML = `
        <div class="card" style="text-align:center; padding:32px 16px;">
          <p style="color:#64748b;">Bạn chưa chia sẻ hồ sơ với phòng khám nào.</p>
        </div>
      `;
      return;
    }

    area.innerHTML = list.map(c => `
      <div class="clinic-card" style="margin-bottom:12px;">
        <div>
          <h4>${c.clinic_name || 'Phòng khám chuyên khoa Da liễu'}</h4>
          <p style="font-size:0.875rem; color:#64748b;">Hồ sơ: <code>${c.case_id.slice(0, 8)}...</code> | Hết hạn: ${c.expires_at ? c.expires_at.split('T')[0] : '30 ngày'}</p>
          <span class="badge-provenance ${c.status === 'active' ? 'badge-user' : 'badge-synthetic'}">
            ${c.status === 'active' ? 'Đang hoạt động (Active)' : 'Đã thu hồi (Revoked)'}
          </span>
          <p style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">Commitment: <code>${c.commitment.slice(0, 18)}...</code></p>
        </div>
        <div>
          ${c.status === 'active' ? `
            <button class="btn btn-danger btn-sm" onclick="window.revokeConsent('${c.id}')">Thu hồi ngay</button>
          ` : `
            <span style="font-size:0.8125rem; color:#94a3b8;">Đã vô hiệu</span>
          `}
        </div>
      </div>
    `).join("");
  } catch (err) {
    document.getElementById("sharing-consents-list").innerHTML = `
      <div class="card"><p style="color:#dc2626;">Lỗi tải danh sách: ${err.message}</p></div>
    `;
  }
}

window.revokeConsent = async (consentId) => {
  if (!confirm("Bạn có chắc chắn muốn thu hồi quyền xem hồ sơ của phòng khám này ngay lập tức?")) return;
  try {
    await apiCall(`/api/consents/${consentId}`, "DELETE");
    alert("Đã thu hồi quyền thành công! Quyền truy cập bị vô hiệu lập tức.");
    renderSharingView(document.getElementById("app-root"));
  } catch (err) {
    alert(`Lỗi thu hồi: ${err.message}`);
  }
};

// -------------------------------------------------------------
// Clinics Directory View
// -------------------------------------------------------------
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
    const list = await apiCall("/api/clinics/nearby?lat=10.7769&lng=106.7009&radius_km=15");
    const area = document.getElementById("clinics-page-list");
    area.innerHTML = list.map(c => ClinicCard(c)).join("");
  } catch (err) {
    document.getElementById("clinics-page-list").innerHTML = `
      ${ClinicCard({ id: "c1", name: "Phòng khám Da liễu Sài Gòn", listing_type: "partner", partner_active: true, distance_km: 1.2, address: "Quận 1, TP.HCM", phone: "028 3829 xxxx" })}
      ${ClinicCard({ id: "c2", name: "Bệnh viện Da liễu TP.HCM", listing_type: "directory", distance_km: 3.5, address: "Quận 3, TP.HCM", phone: "028 3930 8131" })}
    `;
  }
}

// -------------------------------------------------------------
// Web3 Wallet View
// -------------------------------------------------------------
async function renderWalletView(root) {
  root.innerHTML = `
    <div class="card" style="max-width:760px; margin:0 auto;">
      <div class="card-header">
        <h3 class="card-title">Ví Thử Nghiệm Mạng Avalanche (Fuji Testnet)</h3>
        <span class="synthetic-badge">MOCK / DEV WALLET</span>
      </div>
      <div id="wallet-details">
        <p style="color:#64748b;">Đang tải thông tin ví...</p>
      </div>
    </div>
  `;

  try {
    const wallet = await apiCall("/api/wallet");
    const txs = await apiCall("/api/chain/transactions");

    document.getElementById("wallet-details").innerHTML = `
      <div style="background:#f8fafc; padding:16px; border-radius:8px; border:1px solid #e2e8f0; margin-bottom:20px;">
        <p style="font-size:0.875rem; color:#64748b; margin-bottom:4px;">Địa chỉ ví (C-Chain Fuji):</p>
        <code style="font-size:0.95rem; font-weight:600; color:#0f172a;">${wallet.address || '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'}</code>
        <div style="margin-top:12px; display:flex; gap:24px;">
          <div>
            <span style="font-size:0.8125rem; color:#64748b;">Số dư AVAX Testnet:</span>
            <p style="font-size:1.3rem; font-weight:700; color:#10b981;">${wallet.balance || '1.25'} AVAX</p>
          </div>
          <div>
            <span style="font-size:0.8125rem; color:#64748b;">Loại ví:</span>
            <p style="font-size:1.0rem; font-weight:600; color:#0284c7;">${wallet.badge || 'DEV WALLET'}</p>
          </div>
        </div>
      </div>

      <h4 style="margin-bottom:12px;">Nhật Ký Giao Dịch Neo Bằng Chứng (Audit Root Anchors):</h4>
      <table style="width:100%; border-collapse:collapse; font-size:0.8125rem;">
        <tr style="background:#f1f5f9; text-align:left;">
          <th style="padding:6px;">Giao dịch (TxHash)</th>
          <th style="padding:6px;">Loại giao dịch</th>
          <th style="padding:6px;">Trạng thái</th>
        </tr>
        ${txs && txs.length > 0 ? txs.map(t => `
          <tr>
            <td style="padding:6px; border-bottom:1px solid #f1f5f9;"><code>${t.tx_hash ? t.tx_hash.slice(0, 16) + '...' : '0x...'}</code></td>
            <td style="padding:6px; border-bottom:1px solid #f1f5f9;">${t.kind || 'consent_grant'}</td>
            <td style="padding:6px; border-bottom:1px solid #f1f5f9;"><span class="badge-provenance badge-user">${t.status || 'CONFIRMED'}</span></td>
          </tr>
        `).join("") : `
          <tr><td colspan="3" style="padding:12px; text-align:center; color:#64748b;">Chưa có giao dịch neo bằng chứng.</td></tr>
        `}
      </table>
    `;
  } catch (err) {
    document.getElementById("wallet-details").innerHTML = `
      <p style="color:#dc2626;">Lỗi tải thông tin ví: ${err.message}</p>
    `;
  }
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
        <span class="badge-partner">★ VERIFIED PARTNER</span>
      </div>
      <div id="doctor-inbox-list">
        <p style="color:#64748b;">Đang tải danh sách hồ sơ được ủy quyền...</p>
      </div>
    </div>
  `;

  try {
    const list = await apiCall("/api/clinician/inbox");
    const area = document.getElementById("doctor-inbox-list");
    if (!list || list.length === 0) {
      area.innerHTML = `<p style="color:#64748b; padding:16px;">Hiện chưa có bệnh nhân nào gửi hồ sơ.</p>`;
      return;
    }

    area.innerHTML = list.map(c => `
      <div class="clinic-card" style="margin-bottom:12px;">
        <div>
          <h4>Hồ sơ ca: ${c.case_id.slice(0, 8)}... (${c.body_site || 'Vùng da'})</h4>
          <p style="font-size:0.875rem; color:#64748b;">Khởi phát: ${c.profile_type || 'other'} | Hết hạn: ${c.expires_at ? c.expires_at.split('T')[0] : '30 ngày'}</p>
        </div>
        <button class="btn btn-primary btn-sm" onclick="navigate('/doctor/cases/${c.case_id}')">Mở hồ sơ lâm sàng</button>
      </div>
    `).join("");
  } catch (err) {
    document.getElementById("doctor-inbox-list").innerHTML = `
      <div class="card"><p style="color:#dc2626;">Lỗi: ${err.message}. Chỉ bác sĩ thuộc phòng khám Verified Partner mới có thể truy cập.</p></div>
    `;
  }
}

let imageCountdownTimer = null;

async function renderDoctorCaseView(root, caseId) {
  root.innerHTML = `
    <div style="margin-bottom:16px;">
      <a href="#/doctor/inbox" class="btn btn-outline btn-sm">← Hộp thư bác sĩ</a>
    </div>
    <div id="doc-case-detail-content">
      <p style="color:#64748b;">Đang tải hồ sơ lâm sàng và xin token giải mã ảnh...</p>
    </div>
  `;

  try {
    const data = await apiCall(`/api/clinician/cases/${caseId}`);
    const obs = data.observations || [];
    const firstObs = obs[0] || {};
    const imgId = firstObs.image_asset_id;

    let token = null;
    if (imgId) {
      const tokRes = await apiCall(`/api/images/${imgId}/token`, "POST");
      token = tokRes.token;
    }

    const area = document.getElementById("doc-case-detail-content");
    area.innerHTML = `
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
              ${token && imgId ? `
                <img id="doc-image-preview" src="/api/images/${imgId}/content?token=${token}" style="max-width:100%; max-height:260px; border-radius:4px;" />
                <div style="margin-top:6px; font-size:0.8125rem; font-weight:600; color:#0284c7;" id="doc-timer-label">
                  Token hợp lệ trong: <span id="doc-countdown">60</span>s
                </div>
              ` : `
                <p style="color:#64748b; padding:40px 0;">Chưa có ảnh hoặc bệnh nhân chỉ cấp quyền xem chỉ số.</p>
              `}
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
              <textarea class="form-control" id="doc-notes" rows="3" placeholder="Nhập ghi chú chuyên môn cho bệnh nhân..."></textarea>
            </div>
            <button class="btn btn-primary" onclick="window.saveDoctorReview('${caseId}')">Lưu Đánh Giá Bác Sĩ</button>
          </div>
        </div>

        <div style="margin-top:24px; padding-top:16px; border-top:1px solid #e2e8f0;">
          <h4 style="margin-bottom:12px;">Kênh Tư Vấn Trực Tuyến Với Bệnh Nhân:</h4>
          <div id="consult-messages-box" style="height:140px; overflow-y:auto; border:1px solid #e2e8f0; border-radius:6px; padding:10px; background:#f8fafc; margin-bottom:10px;">
            <p style="color:#94a3b8; font-style:italic;">Chưa có tin nhắn nào.</p>
          </div>
          <div style="display:flex; gap:8px;">
            <input type="text" id="consult-msg-input" class="form-control" placeholder="Nhập tin nhắn tư vấn gửi bệnh nhân...">
            <button class="btn btn-primary" onclick="window.sendConsultMsg('${data.consent_id || ''}')">Gửi</button>
          </div>
        </div>
      </div>
    `;

    // 60-second active countdown
    if (token) {
      let secondsLeft = 60;
      if (imageCountdownTimer) clearInterval(imageCountdownTimer);
      imageCountdownTimer = setInterval(() => {
        secondsLeft--;
        const cntEl = document.getElementById("doc-countdown");
        if (cntEl) cntEl.innerText = secondsLeft;
        if (secondsLeft <= 0) {
          clearInterval(imageCountdownTimer);
          const lbl = document.getElementById("doc-timer-label");
          const img = document.getElementById("doc-image-preview");
          if (lbl) lbl.innerHTML = `<span style="color:#dc2626;">Token 60s đã hết hạn. <a href="javascript:renderDoctorCaseView(document.getElementById('app-root'), '${caseId}')">Tải lại</a></span>`;
          if (img) img.style.filter = "blur(8px)";
        }
      }, 1000);
    }
  } catch (err) {
    document.getElementById("doc-case-detail-content").innerHTML = `
      <div class="card" style="border-color:#fca5a5; background:#fef2f2;">
        <h4 style="color:#991b1b;">Truy cập bị từ chối</h4>
        <p style="color:#7f1d1d;">${err.message}</p>
        <p style="font-size:0.875rem; color:#991b1b; margin-top:8px;">Bệnh nhân đã thu hồi quyền truy cập hồ sơ này hoặc thời hạn hiệu lực đã kết thúc.</p>
      </div>
    `;
  }
}

window.saveDoctorReview = async (caseId) => {
  const iga = document.getElementById("doc-iga")?.value || "2";
  const notes = document.getElementById("doc-notes")?.value || "";
  try {
    await apiCall(`/api/clinician/cases/${caseId}/reviews`, "POST", {
      iga_score: parseInt(iga, 10),
      notes: notes
    });
    alert("Đã lưu đánh giá lâm sàng với Provenance: clinician_entered thành công!");
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
};

window.sendConsultMsg = async (consentId) => {
  const input = document.getElementById("consult-msg-input");
  const msg = input?.value?.trim();
  if (!msg) return;
  try {
    await apiCall(`/api/consults/${consentId}/messages`, "POST", { body: msg });
    input.value = "";
    const box = document.getElementById("consult-messages-box");
    if (box) {
      box.innerHTML += `<div style="margin-bottom:6px;"><strong>Bác sĩ:</strong> ${msg}</div>`;
      box.scrollTop = box.scrollHeight;
    }
  } catch (err) {
    alert(`Lỗi gửi tin nhắn: ${err.message}`);
  }
};

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
      <div id="partner-status-box">
        <p style="color:#64748b;">Đang tải trạng thái gói...</p>
      </div>
    </div>
  `;

  try {
    const p = await apiCall("/api/clinic/partner");
    document.getElementById("partner-status-box").innerHTML = `
      <div style="background:#fef3c7; border:1px solid #fde68a; padding:16px; border-radius:8px; margin-bottom:20px;">
        <h4 style="color:#92400e;">Trạng thái gói: ĐANG HOẠT ĐỘNG</h4>
        <p style="font-size:0.875rem; color:#b45309;">Phòng khám: <strong>${p.name || 'Phòng khám Da liễu Sài Gòn'}</strong></p>
        <p style="font-size:0.875rem; color:#b45309;">Hạn sử dụng: <strong>${p.partner_until ? p.partner_until.split('T')[0] : '2026-12-31'}</strong></p>
      </div>
      <div style="margin-bottom:12px; font-size:0.8125rem; color:#64748b;">
        * TEST SETTLEMENT — không phải thanh toán thật. Giao dịch thử nghiệm trên mạng Avalanche C-Chain Fuji.
      </div>
      <button class="btn btn-primary" onclick="window.purchasePartnerDays()">Gia hạn gói 30 ngày (10 DTT Test Token)</button>
    `;
  } catch (err) {
    document.getElementById("partner-status-box").innerHTML = `
      <p style="color:#dc2626;">Lỗi: ${err.message}</p>
    `;
  }
}

window.purchasePartnerDays = async () => {
  try {
    const res = await apiCall("/api/clinic/partner/purchase", "POST", { days: 30 });
    alert(`Gia hạn thành công!\nTxHash: ${res.tx_hash}\nHạn mới: ${res.partner_until?.split('T')[0]}`);
    renderDoctorPartner(document.getElementById("app-root"));
  } catch (err) {
    alert(`Lỗi gia hạn: ${err.message}`);
  }
};

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
      <div id="admin-audit-table">
        <p style="color:#64748b;">Đang tải nhật ký kiểm toán...</p>
      </div>
    </div>
  `;

  try {
    const logs = await apiCall("/api/admin/audit");
    document.getElementById("admin-audit-table").innerHTML = `
      <table style="width:100%; border-collapse:collapse; font-size:0.8125rem;">
        <tr style="background:#f1f5f9; text-align:left;">
          <th style="padding:8px;">Thời gian</th>
          <th style="padding:8px;">Hành động</th>
          <th style="padding:8px;">Tác nhân (Role)</th>
          <th style="padding:8px;">Kết quả</th>
          <th style="padding:8px;">IP (Ẩn danh)</th>
        </tr>
        ${logs.map(l => `
          <tr>
            <td style="padding:8px; border-bottom:1px solid #f1f5f9;">${l.ts ? l.ts.replace('T', ' ').slice(0, 19) : ''}</td>
            <td style="padding:8px; border-bottom:1px solid #f1f5f9;"><code>${l.action}</code></td>
            <td style="padding:8px; border-bottom:1px solid #f1f5f9;">${l.user_role}</td>
            <td style="padding:8px; border-bottom:1px solid #f1f5f9;">
              <span class="badge-provenance ${l.result === 'allow' ? 'badge-user' : 'badge-synthetic'}">${l.result}</span>
            </td>
            <td style="padding:8px; border-bottom:1px solid #f1f5f9;"><code>${l.ip_scrubbed || l.client_ip || '127.0.0.1'}</code></td>
          </tr>
        `).join("")}
      </table>
    `;
  } catch (err) {
    document.getElementById("admin-audit-table").innerHTML = `
      <div class="card" style="border-color:#fca5a5; background:#fef2f2;">
        <h4 style="color:#991b1b;">Truy cập bị từ chối (403 Forbidden)</h4>
        <p style="color:#7f1d1d;">${err.message}</p>
      </div>
    `;
  }
}

async function renderAdminVerification(root) {
  root.innerHTML = `
    <h2 style="margin-bottom:16px;">Phê Duyệt Chứng Chỉ Bác Sĩ & Phòng Khám</h2>
    <div class="card">
      <div id="admin-pending-list">
        <p style="color:#64748b;">Đang tải danh sách chờ phê duyệt...</p>
      </div>
    </div>
  `;

  try {
    const list = await apiCall("/api/admin/clinicians/pending");
    const area = document.getElementById("admin-pending-list");
    if (!list || list.length === 0) {
      area.innerHTML = `<p style="color:#64748b; padding:16px;">Không có hồ sơ nào đang chờ duyệt.</p>`;
      return;
    }

    area.innerHTML = list.map(c => `
      <div class="clinic-card" style="margin-bottom:12px;">
        <div>
          <h4>${c.display_name || c.email}</h4>
          <p style="font-size:0.875rem; color:#64748b;">Phòng khám: ${c.clinic_name || c.clinic_id}</p>
          <span class="badge-provenance badge-synthetic">Chờ phê duyệt</span>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-primary btn-sm" onclick="window.verifyClinicianAction('${c.user_id}', true)">Phê duyệt</button>
          <button class="btn btn-danger btn-sm" onclick="window.verifyClinicianAction('${c.user_id}', false)">Từ chối</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    document.getElementById("admin-pending-list").innerHTML = `
      <div class="card" style="border-color:#fca5a5; background:#fef2f2;">
        <p style="color:#dc2626;">Lỗi: ${err.message}</p>
      </div>
    `;
  }
}

window.verifyClinicianAction = async (userId, isApprove) => {
  const action = isApprove ? "verify" : "reject";
  try {
    await apiCall(`/api/admin/clinicians/${userId}/${action}`, "POST");
    alert(`Đã ${isApprove ? 'phê duyệt' : 'từ chối'} bác sĩ thành công!`);
    renderAdminVerification(document.getElementById("app-root"));
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
};

async function renderAdminSystem(root) {
  root.innerHTML = `
    <h2 style="margin-bottom:16px;">Trạng Thái Hệ Thống (Health & Diagnostics)</h2>
    <div class="grid-3" id="admin-health-cards">
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
        <p style="color:#15803d; font-weight:600; font-size:1.1rem; margin-top:8px;">✓ AVALANCHE FUJI TESTNET</p>
        <span style="font-size:0.75rem; color:#64748b;">Tự động thử lại khi gián đoạn</span>
      </div>
    </div>
  `;
}

// Static Informational Views
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
          <strong>2. Tra cứu đối sánh không mang tính khẳng định:</strong> Danh sách tình trạng tương đồng hiển thị theo thứ tự bảng chữ cái, hoàn toàn không kèm tỷ lệ xác suất (%) hay xếp hạng mức độ nghiêm trọng.
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
      <p style="color:#64748b; margin-top:8px;">Bảo vệ dữ liệu y tế theo nguyên tắc bảo tồn quyền riêng tư và Nghị định 13/2023/NĐ-CP.</p>
    </div>
  `;
}

function renderTerms() {
  return `
    <div class="card" style="max-width:860px; margin:0 auto;">
      <h2>Điều Khoản Dịch Vụ & Cam Kết Trách Nhiệm</h2>
    </div>
  `;
}

function renderOnboarding() {
  return `
    <div class="card" style="max-width:680px; margin:0 auto; text-align:center;">
      <h2>Chào Mừng Đến Với DermaCare Agent</h2>
      <p style="color:#64748b; margin:16px 0;">Ứng dụng theo dõi diễn tiến tổn thương da liễu và hỗ trợ thông tin tham khảo.</p>
      <a href="#/start" class="btn btn-primary">Bắt đầu ngay</a>
    </div>
  `;
}

function renderSettings() {
  return `
    <div class="card" style="max-width:680px; margin:0 auto;">
      <h2>Cài Đặt Tài Khoản & Dữ Liệu</h2>
      <div style="margin-top:20px;">
        <button class="btn btn-outline" onclick="window.exportData()">Xuất toàn bộ dữ liệu cá nhân (JSON)</button>
        <button class="btn btn-danger" style="margin-left:12px;" onclick="window.deleteAccount()">Xóa tài khoản</button>
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
    a.download = `dermacare_export_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
  } catch (err) {
    alert(`Lỗi xuất dữ liệu: ${err.message}`);
  }
};

window.deleteAccount = async () => {
  if (!confirm("Hành động này sẽ vô hiệu hoá tài khoản và ẩn danh toàn bộ dữ liệu. Bạn có chắc chắn không?")) return;
  try {
    await apiCall("/api/me", "DELETE");
    alert("Tài khoản đã được ẩn danh hoá thành công.");
    logout();
  } catch (err) {
    alert(`Lỗi xóa tài khoản: ${err.message}`);
  }
};

// Initial App Boot
document.addEventListener("DOMContentLoaded", () => {
  renderApp();
});
