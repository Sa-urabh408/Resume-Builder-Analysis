/**
 * ResumeAI — Shared JavaScript (ES module)
 * Theme, auth (modular Firebase), API calls, toasts, layout helpers.
 */
import { auth } from "/static/js/firebase-init.js";
import {
  onAuthStateChanged,
  signOut,
} from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";

export { auth };

function displayNameFromUser(user) {
  if (!user) return "";
  const name = (user.displayName || "").trim();
  if (name) return name;
  const email = (user.email || "").trim();
  if (email.includes("@")) return email.split("@")[0];
  return email || "Signed in";
}

function initialFromUser(user) {
  const name = displayNameFromUser(user);
  const ch = name && name[0] ? name[0] : "";
  return ch ? ch.toUpperCase() : "";
}

export function firebaseAuthMessage(err) {
  const code = err && err.code;
  const map = {
    "auth/wrong-password": "Invalid email or password.",
    "auth/user-not-found": "Invalid email or password.",
    "auth/invalid-credential": "Invalid email or password.",
    "auth/email-already-in-use": "An account with this email already exists. Please sign in.",
    "auth/weak-password": "Password should be at least 6 characters.",
    "auth/invalid-email": "Please enter a valid email address.",
    "auth/popup-closed-by-user": "Google sign-in was closed before finishing.",
    "auth/cancelled-popup-request": "Google sign-in was cancelled. Please try again.",
    "auth/popup-blocked": "The sign-in popup was blocked. Allow popups for this site and try again.",
    "auth/network-request-failed": "Network error. Check your connection and try again.",
    "auth/too-many-requests": "Too many attempts. Please try again later.",
    "auth/operation-not-allowed": "This sign-in method is not enabled. Check Firebase Authentication settings.",
  };
  if (code && map[code]) return map[code];
  if (err && err.message) return err.message;
  return "Something went wrong. Please try again.";
}

function initTheme() {
  const savedTheme = localStorage.getItem("resumeai_theme");
  const systemPrefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const activeTheme = savedTheme || (systemPrefersDark ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", activeTheme);
  updateThemeToggleButtons(activeTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const newTheme = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("resumeai_theme", newTheme);
  updateThemeToggleButtons(newTheme);
}

function updateThemeToggleButtons(theme) {
  const btns = document.querySelectorAll(".theme-toggle-btn");
  btns.forEach((btn) => {
    btn.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    btn.setAttribute("title", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    if (theme === "dark") {
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
    } else {
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
    }
  });
}

export let currentUser = null;
export let idToken = null;

let _authPromise = null;

export function waitForAuthUser() {
  if (auth && auth.currentUser) {
    currentUser = auth.currentUser;
    return Promise.resolve(auth.currentUser);
  }
  if (_authPromise) return _authPromise;

  _authPromise = new Promise((resolve) => {
    let resolved = false;
    const timer = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        currentUser = (auth && auth.currentUser) || null;
        resolve(currentUser);
      }
    }, 2500);

    const unsub = onAuthStateChanged(
      auth,
      (user) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timer);
          unsub();
          currentUser = user || null;
          resolve(currentUser);
        }
      },
      (err) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timer);
          unsub();
          console.error("Auth state error:", err);
          resolve(null);
        }
      }
    );
  }).finally(() => {
    setTimeout(() => { _authPromise = null; }, 500);
  });

  return _authPromise;
}

export async function refreshToken(forceRefresh = false) {
  let user = auth ? auth.currentUser : null;
  if (!user) {
    user = await waitForAuthUser();
  }
  if (!user) return null;
  idToken = await user.getIdToken(forceRefresh);
  currentUser = user;
  return idToken;
}

export function getCurrentUser() {
  return auth ? auth.currentUser : null;
}

export function updateTopBarUser(user) {
  const name = displayNameFromUser(user);
  const initial = initialFromUser(user);
  const avatar = document.getElementById("user-avatar");
  if (avatar) {
    avatar.textContent = initial;
    avatar.title = name;
  }
  const topName = document.getElementById("user-name-top");
  if (topName) topName.textContent = name;
  const welcome = document.getElementById("welcome-msg");
  if (welcome && name) welcome.textContent = "Welcome back, " + name;
}

export async function onAuthRequired(arg) {
  let redirectTo = "/login";
  let callback = null;
  if (typeof arg === "function") callback = arg;
  else if (typeof arg === "string" && arg) redirectTo = arg;

  let user;
  try {
    user = await waitForAuthUser();
  } catch (err) {
    console.error(err);
    showToast(firebaseAuthMessage(err), "error");
    window.location.href = redirectTo;
    return null;
  }

  if (!user) {
    const currentPath = window.location.pathname;
    if (currentPath !== "/login" && currentPath !== "/signup" && currentPath !== "/") {
      window.location.href = redirectTo;
    }
    return null;
  }

  currentUser = user;
  try {
    idToken = await user.getIdToken();
  } catch (err) {
    console.error("Could not get ID token:", err);
    showToast("Could not verify your session. Please sign in again.", "error");
    window.location.href = redirectTo;
    return null;
  }

  updateTopBarUser(user);
  if (callback) await callback(user);
  return user;
}

export async function redirectIfLoggedIn(to = "/dashboard") {
  try {
    const user = await waitForAuthUser();
    if (user) window.location.href = to;
  } catch (err) {
    console.error(err);
    showToast(firebaseAuthMessage(err), "error");
  }
}

export async function syncUserProfile(user, extra = {}) {
  const token = await user.getIdToken(true);
  const body = {
    email: extra.email || user.email || "",
    fullName: extra.fullName || user.displayName || "",
    profileImage: extra.profileImage || user.photoURL || "",
  };
  const response = await fetch("/api/auth/profile", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const msg = data.error || "Could not save your profile (" + response.status + ").";
    console.error("Profile sync failed:", msg, data);
    throw new Error(msg);
  }
  return data;
}

export async function logoutUser() {
  sessionStorage.removeItem("lastAnalysis");
  sessionStorage.removeItem("compareIds");
  sessionStorage.removeItem("currentAnalysisId");
  try {
    await signOut(auth);
  } catch (e) {
    console.error("Sign out error:", e);
    showToast(firebaseAuthMessage(e), "error");
  }
  window.location.href = "/login";
}

export async function apiCall(arg1, arg2, body = null, isFormData = false, timeoutMs = 10000) {
  const HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"];
  let method = "GET";
  let url = "";

  if (HTTP_METHODS.includes(String(arg1).toUpperCase())) {
    method = String(arg1).toUpperCase();
    url = arg2;
  } else if (HTTP_METHODS.includes(String(arg2).toUpperCase())) {
    url = arg1;
    method = String(arg2).toUpperCase();
  } else {
    url = arg1;
    method = "GET";
  }

  const heavy = url.includes("/analyze") || url.includes("/api/resume/upload");
  if (heavy) timeoutMs = Math.max(timeoutMs, 60000);

  let token = null;
  try {
    token = await refreshToken();
  } catch (err) {
    console.error("Token refresh failed:", err);
    throw new Error("Could not get a login token. Please sign in again.");
  }

  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  if (!isFormData) headers["Content-Type"] = "application/json";

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const options = { method, headers, signal: controller.signal };
    if (body) options.body = isFormData ? body : JSON.stringify(body);

    const response = await fetch(url, options);
    clearTimeout(timer);

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 401) {
        console.error("Unauthorized (401) from API:", data);
        const path = window.location.pathname;
        if (!path.includes("/login") && !path.includes("/signup") && path !== "/") {
          try { await signOut(auth); } catch (_) {}
          window.location.href = "/login";
        }
      }
      throw new Error(data.error || "Request failed (" + response.status + ")");
    }
    return data;
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") {
      throw new Error("Request timed out. Please check your network and try again.");
    }
    throw err;
  }
}

export function evaluationId(item) {
  if (!item) return "";
  return item.evalId || item.id || "";
}

export function historyEvaluations(payload) {
  if (!payload) return [];
  if (Array.isArray(payload.evaluations)) return payload.evaluations;
  return [];
}

export function showToast(message, type = "info", duration = 4000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast " + type;
  toast.innerHTML = `
    <div style="flex:1;">
      <p style="color:var(--text-primary);font-size:0.875rem;margin:0;line-height:1.4;">${escapeHtml(message)}</p>
    </div>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

export function showLoading(text = "Evaluating resume...") {
  let overlay = document.getElementById("loading-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "loading-overlay";
    overlay.id = "loading-overlay";
    overlay.innerHTML = `
      <div class="loading-card">
        <div class="spinner"></div>
        <p id="loading-text" style="color:var(--text-secondary);margin:0;font-size:0.9rem;">${escapeHtml(text)}</p>
      </div>
    `;
    document.body.appendChild(overlay);
  }
  overlay.querySelector("#loading-text").textContent = text;
  requestAnimationFrame(() => overlay.classList.add("active"));
}

export function hideLoading() {
  const overlay = document.getElementById("loading-overlay");
  if (overlay) overlay.classList.remove("active");
}

export function renderPageError(container, message, onRetry) {
  if (!container) return;
  const msg = message || "Something went wrong.";
  container.innerHTML = `
    <div class="alert alert-error" role="alert" style="display:block;">
      <p style="margin:0 0 0.75rem;">${escapeHtml(msg)}</p>
      ${onRetry ? `<button type="button" class="btn btn-secondary btn-sm" data-retry="1">Retry</button>` : ""}
    </div>
  `;
  const btn = container.querySelector("[data-retry]");
  if (btn && onRetry) btn.addEventListener("click", onRetry);
}

export function renderEmptyEvaluate(container, title, detail) {
  if (!container) return;
  container.innerHTML = `
    <div class="empty-state card" style="display:block;padding:2rem;">
      <h2 style="margin-bottom:0.5rem;">${escapeHtml(title || "Evaluate your resume first")}</h2>
      <p style="color:var(--text-secondary);margin-bottom:1.25rem;">${escapeHtml(detail || "Upload a PDF or DOCX resume to see this page.")}</p>
      <a href="/upload" class="btn btn-primary">Evaluate your resume</a>
    </div>
  `;
}

export function scoreColor(score, max = 100) {
  const pct = (score / max) * 100;
  if (pct >= 85) return "var(--accent)";
  if (pct >= 65) return "var(--color-warning)";
  return "var(--color-danger)";
}

export function renderCircleProgress(containerId, score, max = 100, size = 140) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const strokeWidth = 5;
  const radius = size / 2 - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(score / max, 1);
  const offset = circumference * (1 - pct);
  const color = scoreColor(score, max);

  container.innerHTML = `
    <div class="score-ring-wrap" style="width:${size}px;height:${size}px;">
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="transform:rotate(-90deg);">
        <circle cx="${size / 2}" cy="${size / 2}" r="${radius}"
          fill="none" stroke="var(--border)" stroke-width="${strokeWidth}"/>
        <circle cx="${size / 2}" cy="${size / 2}" r="${radius}"
          fill="none" stroke="${color}" stroke-width="${strokeWidth}"
          stroke-linecap="round"
          stroke-dasharray="${circumference}"
          stroke-dashoffset="${circumference}"
          style="transition:stroke-dashoffset 0.8s ease;"
          class="progress-circle"/>
      </svg>
      <div class="score-ring-label">
        <div class="score-val" style="font-family:var(--font-serif);">${score}</div>
        <div class="score-max">out of ${max}</div>
      </div>
    </div>
  `;
  setTimeout(() => {
    const circle = container.querySelector(".progress-circle");
    if (circle) circle.style.strokeDashoffset = offset;
  }, 50);
}

export function initTabs(tabSelector = ".tab-btn", panelSelector = ".tab-panel") {
  const tabs = document.querySelectorAll(tabSelector);
  const panels = document.querySelectorAll(panelSelector);

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  if (tabs.length > 0 && !document.querySelector(tabSelector + ".active")) {
    tabs[0].click();
  }
}

function initSidebarToggle() {
  const toggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  if (!toggle || !sidebar) return;

  toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  document.addEventListener("click", (e) => {
    if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove("open");
    }
  });
}

function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll(".sidebar-nav .nav-item").forEach((item) => {
    const href = item.getAttribute("href");
    if (href && (href === path || (href !== "/" && path.startsWith(href)))) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

export function skillLevelBadge(level) {
  const map = {
    Beginner: "badge-amber",
    Intermediate: "badge-green",
    Advanced: "badge-green",
    None: "badge-rust",
  };
  return `<span class="badge ${map[level] || "badge-neutral"}">${level}</span>`;
}

export function readinessBadge(status) {
  const map = {
    "Resume Ready": "badge-green",
    "Nearly Ready": "badge-amber",
    Improving: "badge-neutral",
    "Needs Improvement": "badge-rust",
  };
  return `<span class="badge ${map[status] || "badge-neutral"}">${status}</span>`;
}

export function formatDate(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export function saveAnalysisToSession(data) {
  sessionStorage.setItem("lastAnalysis", JSON.stringify(data));
}

export function loadAnalysisFromSession() {
  try {
    return JSON.parse(sessionStorage.getItem("lastAnalysis") || "null");
  } catch (err) {
    console.error("Could not read saved analysis:", err);
    return null;
  }
}

export function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function bootUi() {
  initTheme();
  initSidebarToggle();
  setActiveNav();

  document.querySelectorAll(".theme-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      toggleTheme();
    });
  });

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn && !logoutBtn.dataset.boundLogout) {
    logoutBtn.dataset.boundLogout = "1";
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logoutUser();
    });
  }
}

export function openVideoModal(url, title = 'Video Tutorial', channel = '') {
  let videoId = '';
  if (!url) url = 'https://www.youtube.com';

  if (url.includes('watch?v=')) {
    videoId = url.split('watch?v=')[1].split('&')[0];
  } else if (url.includes('youtu.be/')) {
    videoId = url.split('youtu.be/')[1].split('?')[0];
  } else if (url.includes('embed/')) {
    videoId = url.split('embed/')[1].split('?')[0];
  }

  let modal = document.getElementById('youtube-video-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'youtube-video-modal';
    modal.className = 'custom-video-modal';
    document.body.appendChild(modal);
  }

  const embedSrc = videoId ? `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0` : '';
  const fallbackUrl = url.startsWith('http') ? url : `https://www.youtube.com/results?search_query=${encodeURIComponent(url)}`;

  modal.innerHTML = `
    <div class="video-modal-backdrop" id="video-modal-backdrop-el"></div>
    <div class="video-modal-dialog">
      <div class="video-modal-header">
        <div style="flex:1;min-width:0;padding-right:1rem;">
          <h3 style="font-size:1.05rem;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--text-primary);">${escapeHtml(title)}</h3>
          ${channel ? `<div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem;">By <strong style="color:var(--text-secondary);">${escapeHtml(channel)}</strong> • 100% Free Full Course</div>` : ''}
        </div>
        <button type="button" class="video-modal-close" id="video-modal-close-btn" aria-label="Close modal">✕</button>
      </div>
      <div class="video-modal-body">
        ${videoId ? `
          <div class="video-iframe-wrap">
            <iframe src="${embedSrc}" title="${escapeHtml(title)}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
          </div>
        ` : `
          <div style="padding:2.5rem;text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">▶️</div>
            <p style="color:var(--text-secondary);margin-bottom:1.25rem;">Watch this full course directly on YouTube:</p>
            <a href="${fallbackUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">Open Tutorial on YouTube ↗</a>
          </div>
        `}
      </div>
      <div class="video-modal-footer">
        <span style="font-size:0.78rem;color:var(--text-muted);">ResumeAI Free Learning Partner</span>
        <a href="${fallbackUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="display:inline-flex;align-items:center;gap:0.35rem;text-decoration:none;">
          Open on YouTube.com ↗
        </a>
      </div>
    </div>
  `;

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';

  const closeBtn = document.getElementById('video-modal-close-btn');
  const backdrop = document.getElementById('video-modal-backdrop-el');
  if (closeBtn) closeBtn.onclick = closeVideoModal;
  if (backdrop) backdrop.onclick = closeVideoModal;

  const handleKeydown = (e) => {
    if (e.key === 'Escape') {
      closeVideoModal();
      document.removeEventListener('keydown', handleKeydown);
    }
  };
  document.addEventListener('keydown', handleKeydown);
}

export function closeVideoModal() {
  const modal = document.getElementById('youtube-video-modal');
  if (modal) {
    modal.classList.remove('active');
    modal.innerHTML = '';
  }
  document.body.style.overflow = '';
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootUi);
} else {
  bootUi();
}

window.apiCall = apiCall;
window.onAuthRequired = onAuthRequired;
window.logoutUser = logoutUser;
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.updateTopBarUser = updateTopBarUser;
window.escapeHtml = escapeHtml;
window.formatDate = formatDate;
window.readinessBadge = readinessBadge;
window.skillLevelBadge = skillLevelBadge;
window.renderCircleProgress = renderCircleProgress;
window.saveAnalysisToSession = saveAnalysisToSession;
window.loadAnalysisFromSession = loadAnalysisFromSession;
window.syncUserProfile = syncUserProfile;
window.firebaseAuthMessage = firebaseAuthMessage;
window.redirectIfLoggedIn = redirectIfLoggedIn;
window.historyEvaluations = historyEvaluations;
window.evaluationId = evaluationId;
window.renderPageError = renderPageError;
window.renderEmptyEvaluate = renderEmptyEvaluate;
window.initTabs = initTabs;
window.openVideoModal = openVideoModal;
window.closeVideoModal = closeVideoModal;

// Compatibility bridge for legacy pages
window.firebase = {
  auth: () => ({
    get currentUser() { return auth ? auth.currentUser : null; },
    onAuthStateChanged: (cb) => onAuthStateChanged(auth, cb),
    signOut: () => signOut(auth),
  }),
};
