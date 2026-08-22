(function () {
  "use strict";
  const OLD_ID = "wafd-global-mobile-back";
  const ID = "wafd-mobile-back-v218";
  const HOME_CLASS = "wafd-at-role-home";

  function isMobile() {
    return window.matchMedia("(max-width: 767px)").matches;
  }

  function route() {
    try { return window.frappe?.get_route?.() || []; } catch (_e) { return []; }
  }

  function isHome() {
    const p = window.location.pathname.replace(/\/$/, "");
    const r = route();
    return document.body.classList.contains(HOME_CLASS) ||
      !!document.querySelector(".wafd-role-home, .wafd-role-home-page") ||
      p === "/desk/wafd-role-home" || p === "/app/wafd-role-home" || p === "/wafd-mobile" ||
      r[0] === "wafd-role-home";
  }

  function removeLegacy() {
    document.querySelectorAll("#" + OLD_ID).forEach((n) => n.remove());
  }

  function goBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    if (window.frappe?.set_route) {
      frappe.set_route("wafd-role-home");
      return;
    }
    window.location.assign("/desk/wafd-role-home");
  }

  function createButton() {
    const btn = document.createElement("button");
    btn.id = ID;
    btn.type = "button";
    btn.className = "wafd-mobile-back-v218";
    btn.setAttribute("aria-label", "رجوع");
    btn.setAttribute("title", "رجوع");
    const arrow = document.createElement("span");
    arrow.className = "wafd-mobile-back-v218-arrow";
    arrow.setAttribute("aria-hidden", "true");
    btn.appendChild(arrow);
    btn.addEventListener("click", goBack);
    return btn;
  }

  function syncHomeClass() {
    const detected = !!document.querySelector(".wafd-role-home, .wafd-role-home-page") || route()[0] === "wafd-role-home";
    document.body.classList.toggle(HOME_CLASS, detected);
    return detected;
  }

  function render() {
    if (!document.body) return;
    removeLegacy();
    syncHomeClass();
    let btn = document.getElementById(ID);
    if (!isMobile() || isHome()) {
      if (btn) btn.remove();
      return;
    }
    if (!btn) {
      btn = createButton();
      document.body.appendChild(btn);
    }
  }

  function boot() {
    if (!document.body) return;
    render();
    const observer = new MutationObserver(() => requestAnimationFrame(render));
    observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener("popstate", () => setTimeout(render, 0));
    window.addEventListener("pageshow", () => setTimeout(render, 0));
    window.addEventListener("resize", render);
    if (window.frappe?.router?.on) {
      frappe.router.on("change", () => {
        document.body.classList.remove(HOME_CLASS);
        setTimeout(render, 0);
        setTimeout(render, 120);
      });
    }
    // Remove legacy cached button repeatedly during initial Frappe route restore.
    [50, 150, 350, 700, 1200, 2200].forEach((ms) => setTimeout(render, ms));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
