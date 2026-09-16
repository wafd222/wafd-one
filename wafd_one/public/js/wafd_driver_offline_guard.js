(function () {
  "use strict";

  const NETWORK_TEXT = /connection\s+lost|not\s+connected\s+to\s+(the\s+)?internet|network\s+error|offline/i;
  let observer = null;

  function driverOnly() {
    const frappe = window.frappe;
    const user = String(frappe?.session?.user || "");
    if (!user || user === "Guest") return false;
    const roles = new Set(frappe?.user_roles || []);
    if (!roles.has("WAFD Driver") || roles.has("System Manager") || roles.has("WAFD Operations Manager")) return false;
    return ![...roles].some((role) => String(role).startsWith("WAFD ") && !["WAFD Driver", "WAFD Cleaning Supervisor", "WAFD Delivery Viewer"].includes(role));
  }

  function messageText(value) {
    if (typeof value === "string") return value;
    if (!value) return "";
    if (typeof value === "object") {
      return [value.title, value.message, value.indicator, value.primary_action?.label].filter(Boolean).join(" ");
    }
    return String(value);
  }

  function isConnectionNotice(args) {
    return driverOnly() && NETWORK_TEXT.test(args.map(messageText).join(" "));
  }

  function patch(name) {
    const frappe = window.frappe;
    const original = frappe?.[name];
    if (typeof original !== "function" || original.__wafdDriverOfflineGuard) return;
    const wrapped = function (...args) {
      if (isConnectionNotice(args)) {
        window.dispatchEvent(new CustomEvent("wafd-driver-connectivity", {detail:{online:false, source:"frappe-network-notice"}}));
        return undefined;
      }
      return original.apply(this, args);
    };
    wrapped.__wafdDriverOfflineGuard = true;
    wrapped.__wafdOriginal = original;
    frappe[name] = wrapped;
  }

  function removeConnectionToasts(root=document) {
    if (!driverOnly()) return;
    const selectors = [
      ".alert", ".toast", ".frappe-toast", ".desk-alert", ".msgprint", ".modal-dialog"
    ];
    root.querySelectorAll?.(selectors.join(",")).forEach((node) => {
      if (NETWORK_TEXT.test(String(node.textContent || ""))) node.remove();
    });
  }

  function syncState() {
    if (!document.body) return;
    const active = driverOnly() && !navigator.onLine;
    document.body.classList.toggle("wafd-driver-is-offline", active);
    window.dispatchEvent(new CustomEvent("wafd-driver-connectivity", {detail:{online:navigator.onLine}}));
    if (active) removeConnectionToasts();
  }

  function install() {
    patch("show_alert");
    patch("msgprint");
    if (!observer && document.body) {
      observer = new MutationObserver((records) => {
        if (!driverOnly()) return;
        for (const record of records) {
          for (const node of record.addedNodes || []) {
            if (!(node instanceof Element)) continue;
            if (NETWORK_TEXT.test(String(node.textContent || ""))) removeConnectionToasts(node.parentElement || document);
          }
        }
      });
      observer.observe(document.body, {childList:true, subtree:true});
    }
    syncState();
  }

  window.addEventListener("offline", syncState);
  window.addEventListener("online", syncState);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, {once:true});
  else install();
  window.setTimeout(install, 1200);
})();
