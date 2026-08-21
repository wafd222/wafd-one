(function () {
  const HOME = '/desk/wafd-role-home';
  const ID = 'wafd-global-mobile-back';

  function isMobile() {
    return window.matchMedia('(max-width: 767px)').matches;
  }

  function route() {
    try { return window.frappe?.get_route?.() || []; } catch (e) { return []; }
  }

  function isHome() {
    const p = location.pathname.replace(/\/$/, '');
    return p === HOME || p === '/app/wafd-role-home' || p === '/wafd-mobile' || route()[0] === 'wafd-role-home';
  }

  function goBack() {
    // Match native iOS/browser navigation when history is available.
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    if (window.frappe?.set_route) {
      frappe.set_route('wafd-role-home');
      return;
    }
    window.location.assign(HOME);
  }

  function createButton() {
    const btn = document.createElement('button');
    btn.id = ID;
    btn.type = 'button';
    btn.className = 'wafd-global-mobile-back';
    btn.setAttribute('aria-label', 'رجوع');
    btn.setAttribute('title', 'رجوع');
    btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.15" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    btn.addEventListener('click', goBack);
    return btn;
  }

  function render() {
    let btn = document.getElementById(ID);
    if (!isMobile() || isHome()) {
      if (btn) btn.remove();
      return;
    }

    if (!btn) btn = createButton();

    // RC193: mount on the page layer, never inside Frappe's navbar/flex layout.
    // position:fixed in CSS guarantees zero layout width/height consumption.
    const host = document.body;
    if (btn.parentElement !== host) host.appendChild(btn);
  }

  // RC207: keep an entry guard alive until Frappe has finished restoring its
  // initial route. Safari/Frappe may restore the last open Form *after* our
  // first redirect. We therefore redirect any initial non-home route back to
  // role home and only release the guard after home has stayed stable briefly.
  const entryGuard = {
    active: true,
    deadline: Date.now() + 10000,
    homeSeenAt: 0,
    redirecting: false,
    timer: null,
  };

  function isRestrictedUndertakingOfficer() {
    const roles = window.frappe?.user_roles || [];
    return roles.includes('WAFD Undertaking Officer') &&
      !roles.includes('System Manager') && !roles.includes('WAFD Operations Manager');
  }

  function releaseEntryGuardSoon() {
    clearTimeout(entryGuard.timer);
    entryGuard.timer = setTimeout(() => {
      if (isHome()) entryGuard.active = false;
    }, 900);
  }

  function enforceInitialUndertakingHome() {
    if (!entryGuard.active || !isMobile()) return;
    if (Date.now() > entryGuard.deadline) { entryGuard.active = false; return; }
    const roles = window.frappe?.user_roles || [];
    if (!roles.length) { setTimeout(enforceInitialUndertakingHome, 120); return; }
    if (!isRestrictedUndertakingOfficer()) { entryGuard.active = false; return; }

    if (isHome()) {
      if (!entryGuard.homeSeenAt) entryGuard.homeSeenAt = Date.now();
      releaseEntryGuardSoon();
      return;
    }

    // If Frappe restores a last-open form after our first redirect, cancel the
    // pending release and route home again. The redirect lock prevents loops.
    entryGuard.homeSeenAt = 0;
    clearTimeout(entryGuard.timer);
    if (entryGuard.redirecting) return;
    entryGuard.redirecting = true;
    try {
      if (window.frappe?.set_route) frappe.set_route('wafd-role-home');
      else window.location.replace(HOME);
    } finally {
      setTimeout(() => { entryGuard.redirecting = false; enforceInitialUndertakingHome(); }, 180);
    }
  }

  document.addEventListener('DOMContentLoaded', () => { setTimeout(render, 60); setTimeout(enforceInitialUndertakingHome, 100); });
  window.addEventListener('popstate', () => setTimeout(render, 60));
  window.addEventListener('resize', render);
  if (window.frappe?.router?.on) frappe.router.on('change', () => { setTimeout(render, 80); setTimeout(enforceInitialUndertakingHome, 20); });
  setTimeout(render, 250);
  setTimeout(enforceInitialUndertakingHome, 320);
  setTimeout(enforceInitialUndertakingHome, 900);
  window.addEventListener('pageshow', () => setTimeout(enforceInitialUndertakingHome, 40));
  window.addEventListener('focus', () => setTimeout(enforceInitialUndertakingHome, 40));
})();
