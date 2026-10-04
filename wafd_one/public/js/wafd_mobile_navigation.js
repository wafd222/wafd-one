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
  const CLEANING_ROUTE = "wafd-cleaning-home";
  const CLEANING_CLASS = "wafd-at-cleaning-home";
  const VIEWER_ROUTE = "wafd-delivery-viewer";
  const VIEWER_CLASS = "wafd-at-delivery-viewer";
  const DELIVERY_REPORT_ROUTE = "wafd-delivery-report";
  const DELIVERY_REPORT_CLASS = "wafd-at-delivery-report";
  const DELIVERY_SUPERVISOR_ROUTE = "wafd-delivery-supervisor";
  const DELIVERY_SUPERVISOR_CLASS = "wafd-at-delivery-supervisor";
  const LOADING_CLASS = "wafd-at-loading-record";
  const DOCUMENT_SHELL_CLASS = "wafd-mobile-document-shell";
  const FIELD_APPBAR_ID = "wafd-field-appbar-rc278";
  const FIELD_ROLES = new Set(["WAFD Driver", "WAFD Cleaning Supervisor", "WAFD Delivery Viewer"]);
  const FIELD_ROUTES = new Set([HOME_ROUTE, DRIVER_ROUTE, CLEANING_ROUTE, VIEWER_ROUTE]);
  const LANGUAGES = {ar:"العربية",en:"English",id:"Bahasa Indonesia",ur:"اردو",hi:"हिन्दी",bn:"বাংলা",fr:"Français",ha:"Hausa",sw:"Kiswahili",uz:"O‘zbekcha"};
  const FIELD_LABELS = {
    ar:{menu:"القائمة",language:"اللغة",logout:"تسجيل الخروج",home:"الصفحة الرئيسية"},
    en:{menu:"Menu",language:"Language",logout:"Logout",home:"Home"},
    id:{menu:"Menu",language:"Bahasa",logout:"Keluar",home:"Beranda"},
    ur:{menu:"مینو",language:"زبان",logout:"لاگ آؤٹ",home:"ہوم"},
    hi:{menu:"मेनू",language:"भाषा",logout:"लॉग आउट",home:"होम"},
    bn:{menu:"মেনু",language:"ভাষা",logout:"লগ আউট",home:"হোম"},
    fr:{menu:"Menu",language:"Langue",logout:"Déconnexion",home:"Accueil"},
    ha:{menu:"Menu",language:"Harshe",logout:"Fita",home:"Gida"},
    sw:{menu:"Menyu",language:"Lugha",logout:"Ondoka",home:"Nyumbani"},
    uz:{menu:"Menyu",language:"Til",logout:"Chiqish",home:"Bosh sahifa"},
  };

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
    if (r[0] === "Page" && r[1]) return String(r[1]).trim();
    return r.length ? String(r[0] || "").trim() : "";
  }

  function pathIsRoute(routeName) {
    const path = String(window.location.pathname || "").replace(/\/$/, "");
    return path === `/app/${routeName}` || path === `/desk/${routeName}`;
  }

  function isFieldOnlyUser() {
    const user = String(window.frappe?.session?.user || "");
    if (!user || user === "Guest") return false;
    const roles = new Set(window.frappe?.user_roles || []);
    if (![...FIELD_ROLES].some((role) => roles.has(role))) return false;
    if (roles.has("System Manager")) return false;
    return ![...roles].some((role) => String(role).startsWith("WAFD ") && !FIELD_ROLES.has(role));
  }

  function fieldRouteIsAllowed() {
    const routeName = currentRouteName();
    if (routeName) return FIELD_ROUTES.has(routeName);
    return [...FIELD_ROUTES].some(pathIsRoute);
  }

  function enforceFieldHome() {
    if (!isFieldOnlyUser() || fieldRouteIsAllowed()) return false;
    const path = String(window.location.pathname || "").replace(/\/$/, "");
    if (path === "/app" || path === "/desk" || path === "/app/home" || path === "/app/wafd-one") {
      window.location.replace("/app/wafd-role-home");
      return true;
    }
    if (window.frappe?.set_route) {
      frappe.set_route(HOME_ROUTE);
      return true;
    }
    window.location.replace("/app/wafd-role-home");
    return true;
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

  function isCleaningHome() {
    const routeName = currentRouteName();
    if (routeName) return routeName === CLEANING_ROUTE;
    return pathIsRoute(CLEANING_ROUTE);
  }

  function isDeliveryViewer() {
    const routeName = currentRouteName();
    if (routeName) return routeName === VIEWER_ROUTE;
    const path = String(window.location.pathname || "").replace(/\/$/, "");
    return path === "/desk/wafd-delivery-viewer" || path === "/app/wafd-delivery-viewer";
  }

  function isDeliveryReport() {
    const routeName = currentRouteName();
    if (routeName) return routeName === DELIVERY_REPORT_ROUTE;
    return pathIsRoute(DELIVERY_REPORT_ROUTE);
  }

  function isDeliverySupervisorPage() {
    const routeName = currentRouteName();
    if (routeName) return routeName === DELIVERY_SUPERVISOR_ROUTE;
    return pathIsRoute(DELIVERY_SUPERVISOR_ROUTE);
  }

  function isDeliverySupervisorShell() {
    const roles = new Set(window.frappe?.user_roles || []);
    return roles.has("WAFD Delivery Supervisor")
      && !roles.has("System Manager")
      && !roles.has("WAFD Operations Manager");
  }

  function isLoadingRecordForm() {
    const route = currentRoute();
    return route[0] === "Form" && route[1] === "WAFD Loading Record";
  }

  function isUndertakingRoute() {
    const route = currentRoute();
    return (route[0] === "Form" || route[0] === "List") && route[1] === "WAFD Hotel Undertaking";
  }


  function isStandalonePwa() {
    return !!(
      window.wafdIsStandalone ||
      window.navigator.standalone === true ||
      window.matchMedia?.("(display-mode: standalone)")?.matches
    );
  }

  function syncPwaChrome(home, documentShell = false) {
    if (!document.body) return;
    // The WAFD shell must be identical in an installed iPhone/Android PWA and
    // in a normal Android browser tab.  Restricting this to standalone mode
    // exposed Frappe's sidebar, extra workspaces and removed the language menu.
    const hide = !!(home && isMobile());
    const compactDocument = !!(documentShell && isMobile());
    // This runtime class is the single source of truth for the RC234 shell.
    // Do not make the CSS depend on a second class populated by another asset:
    // on iOS those assets can finish in a different order after a cold launch.
    document.body.classList.toggle(PWA_SHELL_CLASS, hide);
    document.body.classList.toggle(DOCUMENT_SHELL_CLASS, compactDocument);
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
      const isDocumentHeader = node.matches?.(".page-head, .desk-header, .app-header, .mobile-header, .mobile-navbar");
      const shouldHide = hide || (compactDocument && !isDocumentHeader);
      if (shouldHide) {
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

  function fieldLanguage() {
    const selected = String(localStorage.getItem("wafd_lang") || "ar");
    return LANGUAGES[selected] ? selected : "ar";
  }

  function createFieldAppbar() {
    const lang = fieldLanguage();
    const labels = FIELD_LABELS[lang] || FIELD_LABELS.en;
    const bar = document.createElement("section");
    bar.id = FIELD_APPBAR_ID;
    bar.className = "wafd-pwa-appbar wafd-field-appbar";
    bar.setAttribute("aria-label", "WAFD ONE");
    const user = String(window.frappe?.session?.user || "");
    bar.innerHTML = `<button type="button" class="wafd-pwa-menu-btn" aria-label="${labels.menu}" aria-expanded="false"><span></span><span></span><span></span></button><button type="button" class="wafd-pwa-brand-home" aria-label="${labels.home}">WAFD ONE</button><div class="wafd-pwa-menu" role="menu" hidden><button type="button" data-wafd-field-home>⌂ <span>${labels.home}</span></button><label class="wafd-pwa-language-row" for="wafd-field-language"><span>文 ${labels.language}</span><select id="wafd-field-language">${Object.entries(LANGUAGES).map(([code,name])=>`<option value="${code}" ${code===lang?"selected":""}>${name}</option>`).join("")}</select></label><div class="wafd-pwa-account"><small>${labels.menu}</small><b>${user}</b></div><button type="button" class="is-danger" data-wafd-field-logout>↪ <span>${labels.logout}</span></button></div>`;
    const menu = bar.querySelector(".wafd-pwa-menu");
    const menuButton = bar.querySelector(".wafd-pwa-menu-btn");
    const close = () => { menu.hidden = true; menuButton.setAttribute("aria-expanded", "false"); };
    menuButton.addEventListener("click", (event) => {
      event.stopPropagation();
      menu.hidden = !menu.hidden;
      menuButton.setAttribute("aria-expanded", menu.hidden ? "false" : "true");
    });
    bar.querySelector(".wafd-pwa-brand-home").addEventListener("click", () => frappe.set_route(HOME_ROUTE));
    bar.querySelector("[data-wafd-field-home]").addEventListener("click", () => { close(); frappe.set_route(HOME_ROUTE); });
    bar.querySelector("#wafd-field-language").addEventListener("change", async function () {
      localStorage.setItem("wafd_lang", this.value);
      await frappe.call({method:"wafd_one.language.set_user_language", args:{language:this.value}, freeze:true});
      window.location.reload();
    });
    bar.querySelector("[data-wafd-field-logout]").addEventListener("click", () => {
      close();
      if (frappe.app?.logout) frappe.app.logout();
      else window.location.assign("/?cmd=web_logout");
    });
    document.addEventListener("click", (event) => {
      if (document.getElementById(FIELD_APPBAR_ID) === bar && !bar.contains(event.target)) close();
    });
    return bar;
  }

  function syncFieldAppbar(show) {
    let bar = document.getElementById(FIELD_APPBAR_ID);
    if (!show || !isMobile()) {
      if (bar) bar.remove();
      return;
    }
    if (!bar) {
      bar = createFieldAppbar();
      const activePage = Array.from(document.querySelectorAll(".page-container")).find(elementIsActuallyVisible);
      (activePage || document.body).prepend(bar);
    }
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
    if (enforceFieldHome()) return;
    const home = isHome();
    const employeeTeam = isEmployeeTeam();
    const driverTrips = isDriverTrips();
    const cleaningHome = isCleaningHome();
    const deliveryViewer = isDeliveryViewer();
    const deliveryReport = isDeliveryReport();
    const deliverySupervisorPage = isDeliverySupervisorPage();
    const deliverySupervisorShell = (deliveryReport || deliverySupervisorPage) && isDeliverySupervisorShell();
    const loadingRecord = isLoadingRecordForm();
    const undertakingRoute = isUndertakingRoute();
    syncHomeState(home);
    document.body.classList.toggle(EMPLOYEE_CLASS, employeeTeam);
    document.body.classList.toggle(DRIVER_CLASS, driverTrips);
    document.body.classList.toggle(CLEANING_CLASS, cleaningHome);
    document.body.classList.toggle(VIEWER_CLASS, deliveryViewer);
    document.body.classList.toggle(DELIVERY_REPORT_CLASS, deliveryReport && deliverySupervisorShell);
    document.body.classList.toggle(DELIVERY_SUPERVISOR_CLASS, deliverySupervisorPage && deliverySupervisorShell);
    document.body.classList.toggle(LOADING_CLASS, loadingRecord);
    syncPwaChrome(home || driverTrips || cleaningHome || deliveryViewer || deliverySupervisorShell, undertakingRoute);
    syncFieldAppbar(driverTrips || cleaningHome || deliverySupervisorShell || undertakingRoute);

    let btn = document.getElementById(ID);
    if (!isMobile() || home || employeeTeam || driverTrips || cleaningHome || deliveryViewer || loadingRecord || hasOpenModal()) {
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
        enforceFieldHome();
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
