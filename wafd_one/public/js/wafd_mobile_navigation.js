(function () {
  "use strict";

  const LEGACY_IDS = ["wafd-global-mobile-back", "wafd-mobile-back-v218"];
  const ID = "wafd-mobile-back-v219";
  const HOME_CLASS = "wafd-at-role-home";
  const PWA_SHELL_CLASS = "wafd-pwa-home-shell";
  const HOME_ROUTE = "wafd-role-home";
  const EMPLOYEE_ROUTE = "wafd-employee-team";
  const EMPLOYEE_CLASS = "wafd-at-employee-team";

  function isMobile() {
    return window.matchMedia("(max-width: 767px)").matches;
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


  function isStandalonePwa() {
    return !!(
      window.wafdIsStandalone ||
      window.navigator.standalone === true ||
      window.matchMedia?.("(display-mode: standalone)")?.matches
    );
  }

  function syncPwaChrome(home) {
    if (!document.body) return;
    const hide = !!(home && isMobile() && isStandalonePwa());
    // This runtime class is the single source of truth for the RC234 shell.
    // Do not make the CSS depend on a second class populated by another asset:
    // on iOS those assets can finish in a different order after a cold launch.
    document.body.classList.toggle(PWA_SHELL_CLASS, hide);
    // Frappe can mount its navbar after our stylesheet/route callback. Direct
    // inline display is therefore used as a deterministic fallback, but only
    // on standalone role home. Remove it immediately on every other route.
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
    return Array.from(document.querySelectorAll(".modal.show, .modal[style*='display: block'], .frappe-dialog"))
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
    window.location.assign("/desk/wafd-role-home");
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
    syncHomeState(home);
    document.body.classList.toggle(EMPLOYEE_CLASS, employeeTeam);
    syncPwaChrome(home);

    let btn = document.getElementById(ID);
    if (!isMobile() || home || employeeTeam || hasOpenModal()) {
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
