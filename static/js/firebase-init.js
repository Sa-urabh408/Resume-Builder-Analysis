/**
 * One Firebase setup for the whole site.
 * Modular SDK 12.19.0 — import this file; do not use firebase-compat.
 */
import { initializeApp, getApps } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";

function showFirebaseConfigError(message) {
  console.error("[Firebase]", message);
  if (document.getElementById("firebase-config-error")) return;
  const banner = document.createElement("div");
  banner.id = "firebase-config-error";
  banner.setAttribute("role", "alert");
  banner.style.cssText = [
    "position:fixed",
    "top:0",
    "left:0",
    "right:0",
    "z-index:99999",
    "padding:0.85rem 1.25rem",
    "background:#8B2E2E",
    "color:#fff",
    "font-family:system-ui,sans-serif",
    "font-size:0.9rem",
    "line-height:1.45",
  ].join(";");
  banner.textContent = message;
  const mount = () => {
    if (!document.getElementById("firebase-config-error")) {
      document.body.prepend(banner);
    }
  };
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
}

function readConfig() {
  const raw = window.FIREBASE_CONFIG || {};
  return {
    apiKey: String(raw.apiKey || "").trim(),
    authDomain: String(raw.authDomain || "").trim(),
    projectId: String(raw.projectId || "").trim(),
    storageBucket: String(raw.storageBucket || "").trim(),
    messagingSenderId: String(raw.messagingSenderId || "").trim(),
    appId: String(raw.appId || "").trim(),
  };
}

const REQUIRED = ["apiKey", "authDomain", "projectId", "appId"];
const config = readConfig();
const missing = REQUIRED.filter((key) => !config[key]);

if (missing.length) {
  showFirebaseConfigError(
    "Firebase is not configured. Missing: " +
      missing.join(", ") +
      ". Add these values to the Flask .env file and restart the server."
  );
  throw new Error("Firebase config missing: " + missing.join(", "));
}

const app = getApps().length ? getApps()[0] : initializeApp(config);
export const auth = getAuth(app);
