(function () {
  "use strict";

  const LEGACY_IDS = ["wafd-global-mobile-back", "wafd-mobile-back-v218"];
  const ID = "wafd-mobile-back-v219";
  const HOME_CLASS = "wafd-at-role-home";
  const PWA_SHELL_CLASS = "wafd-pwa-home-shell";
  const HOME_ROUTE = "wafd-role-home";
  const EMPLOYEE_ROUTE = "wafd-employee-team";
  const EMPLOYEE_CLASS = "wafd-at-employee-team";
  const DRIVER_ROUTE = "wafd-driver-trips";
  const DRIVER_CLASS = "wafd-at-driver-trips";
  const VIEWER_ROUTE = "wafd-delivery-viewer";
  const VIEWER_CLASS = "wafd-at-delivery-viewer";
  const LOADING_CLASS = "wafd-at-loading-record";

  function isMobile() {
    const mobileUa = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || "");
    const touchDevice = (navigator.maxTouchPoints || 0) > 0 && window.screen.width <= 1200;
    return window.matchMedia("(max-width: 900px)").matches || mobileUa || touchDevice;
  }

  function currentRoute() {
    try {
      const r = window.frappe?.get_route?.();
      return Array.isArray(r) ? r : [];
    } catch (_e) {
      return [];
    }
  }

  function currentRouteName() {
    const r = currentRoute();
    return r.length ? String(r[0] || "").trim() : "";
  }

  function pathIsHome() {
    const p = String(window.location.pathname || "").replace(/\/$/, "");
    return p === "/desk/wafd-role-home" || p === "/app/wafd-role-home" || p === "/wafd-mobile";
  }

  function elementIsActuallyVisible(el) {
    if (!el) return false;
    // Frappe Desk is an SPA and keeps previously visited pages mounted but hidden.
    // Only use DOM visibility as a last-resort fallback before the router is ready.
    if (el.closest(".hide, [hidden], [aria-hidden='true']")) return false;
    const style = window.getComputedStyle ? window.getComputedStyle(el) : null;
    if (style && (style.display === "none" || style.visibility === "hidden")) return false;
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects?.().length);
  }

  function visibleHomeFallback() {
    return Array.from(document.querySelectorAll(".wafd-role-home-page, .wafd-role-home"))
      .some(elementIsActuallyVisible);
  }

  function isHome() {
    // Route is the source of truth inside Frappe Desk. Do NOT infer home merely
    // because a hidden cached home page still exists in the SPA DOM.
    const routeName = currentRouteName();
    if (routeName) return routeName === HOME_ROUTE;
    if (pathIsHome()) return true;
    return visibleHomeFallback();
  }

  function isEmployeeTeam() {
    const routeName = currentRouteName();
    if (routeName) return routeName === EMPLOYEE_ROUTE;
    const path = String(window.location.pathname || "").replace(/\/$/, "");
    return path === "/desk/wafd-employee-team" || path === "/app/wafd-employee-team";
  }

  function isDriverTrips() {
    const routeName = currentRouteName();
    if (routeName) return routeName === DRIVER_ROUTE;
    const path = String(window.location.pathname || "").replace(/\/$/, "");
    return path === "/desk/wafd-driver-trips" || path === "/app/wafd-driver-trips";
  }

  function isDeliveryViewer() {
    const routeName = currentRouteName();
    if (routeName) return routeName === VIEWER_ROUTE;
    const path = String(window.location.pathname || "").replace(/\/$/, "");
    return path === "/desk/wafd-delivery-viewer" || path === "/app/wafd-delivery-viewer";
  }

  function isLoadingRecordForm() {
    const route = currentRoute();
    return route[0] === "Form" && route[1] === "WAFD Loading Record";
  }


  function isStandalonePwa() {
    return !!(
      window.wafdIsStandalone ||
      window.navigator.standalone === true ||
      window.matchMedia?.("(display-mode: standalone)")?.matches
    );
  }

  function syncPwaChrome(home) {
    if (!document.body) return;
    // The WAFD shell must be identical in an installed iPhone/Android PWA and
    // in a normal Android browser tab.  Restricting this to standalone mode
    // exposed Frappe's sidebar, extra workspaces and removed the language menu.
    const hide = !!(home && isMobile());
    // This runtime class is the single source of truth for the RC234 shell.
    // Do not make the CSS depend on a second class populated by another asset:
    // on iOS those assets can finish in a different order after a cold launch.
    document.body.classList.toggle(PWA_SHELL_CLASS, hide);
    // Frappe can mount its navbar after our stylesheet/route callback. Direct
    // inline display is therefore used as a deterministic fallback, but only
    // on the mobile role home. Remove it immediately on every other route.
    document.querySelectorAll(
      [
        ".navbar",
        "header.navbar",
        ".desk-navbar",
        ".page-head",
        ".desk-header",
        ".app-header",
        ".mobile-header",
        ".mobile-navbar",
        "body > header",
        ".layout-side-section",
        ".standard-sidebar",
        ".desk-sidebar",
        ".body-sidebar",
        ".body-sidebar-container",
        ".sidebar-overlay",
        ".sidebar-backdrop",
      ].join(", ")
    ).forEach((node) => {
      if (hide) {
        if (!node.hasAttribute("data-wafd-prev-display")) {
          node.setAttribute("data-wafd-prev-display", node.style.display || "");
        }
        node.style.setProperty("display", "none", "important");
      } else if (node.hasAttribute("data-wafd-prev-display")) {
        const previous = node.getAttribute("data-wafd-prev-display") || "";
        node.style.removeProperty("display");
        if (previous) node.style.display = previous;
        node.removeAttribute("data-wafd-prev-display");
      }
    });
  }

  function hasOpenModal() {
    return Array.from(document.querySelectorAll(".modal.show, .modal[style*='display: block'], .frappe-dialog, .wafd-und-preview-overlay"))
      .some(elementIsActuallyVisible);
  }

  function removeLegacy() {
    LEGACY_IDS.forEach((legacyId) => {
      document.querySelectorAll("#" + legacyId).forEach((node) => node.remove());
    });
  }

  function goBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    if (window.frappe?.set_route) {
      frappe.set_route(HOME_ROUTE);
      return;
    }
    window.location.assign("/app/wafd-role-home");
  }

  function createButton() {
    const btn = document.createElement("button");
    btn.id = ID;
    btn.type = "button";
    btn.className = "wafd-mobile-back-v219";
    btn.setAttribute("aria-label", "رجوع");
    btn.setAttribute("title", "رجوع");

    // Pure CSS geometry avoids font/SVG rendering issues on iOS Safari.
    const arrow = document.createElement("span");
    arrow.className = "wafd-mobile-back-v219-arrow";
    arrow.setAttribute("aria-hidden", "true");
    btn.appendChild(arrow);
    btn.addEventListener("click", goBack);
    return btn;
  }

  function syncHomeState(home) {
    document.body.classList.toggle(HOME_CLASS, !!home);
  }

  function render() {
    if (!document.body) return;

    removeLegacy();
    const home = isHome();
    const employeeTeam = isEmployeeTeam();
    const driverTrips = isDriverTrips();
    const deliveryViewer = isDeliveryViewer();
    const loadingRecord = isLoadingRecordForm();
    syncHomeState(home);
    document.body.classList.toggle(EMPLOYEE_CLASS, employeeTeam);
    document.body.classList.toggle(DRIVER_CLASS, driverTrips);
    document.body.classList.toggle(VIEWER_CLASS, deliveryViewer);
    document.body.classList.toggle(LOADING_CLASS, loadingRecord);
    syncPwaChrome(home || deliveryViewer);

    let btn = document.getElementById(ID);
    if (!isMobile() || home || employeeTeam || driverTrips || deliveryViewer || loadingRecord || hasOpenModal()) {
      if (btn) btn.remove();
      return;
    }

    if (!btn) {
      btn = createButton();
      document.body.appendChild(btn);
    }
  }

  function scheduleRender() {
    requestAnimationFrame(render);
  }

  function boot() {
    if (!document.body) return;
    render();

    // DOM changes can happen after Frappe route changes; rerender without using
    // stale hidden page nodes to determine the active screen.
    const observer = new MutationObserver(scheduleRender);
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "hidden", "aria-hidden"] });

    window.addEventListener("popstate", () => setTimeout(render, 0));
    window.addEventListener("pageshow", () => setTimeout(render, 0));
    window.addEventListener("resize", render);

    if (window.frappe?.router?.on) {
      frappe.router.on("change", () => {
        setTimeout(render, 0);
        setTimeout(render, 80);
        setTimeout(render, 220);
      });
    }

    [50, 150, 350, 700, 1200, 2200].forEach((ms) => setTimeout(render, ms));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
