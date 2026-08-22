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
    const r = route();
    // RC216: DOM detection is the final authority because Frappe/Safari can
    // temporarily report /app or a stale route while the role-home page is
    // already mounted. Never show a back button on the actual home screen.
    if (document.querySelector('.wafd-role-home')) return true;
    return p === HOME || p === '/app/wafd-role-home' || p === '/wafd-mobile' || r[0] === 'wafd-role-home';
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

    // RC216: draw the arrow from CSS borders rather than a font glyph, SVG,
    // pseudo-element, or icon font. This survives iOS Safari text/icon quirks.
    const arrow = document.createElement('span');
    arrow.setAttribute('aria-hidden', 'true');
    arrow.style.cssText = [
      'display:block!important',
      'width:13px!important',
      'height:13px!important',
      'box-sizing:border-box!important',
      'border-left:3px solid #765b20!important',
      'border-bottom:3px solid #765b20!important',
      'border-top:0!important',
      'border-right:0!important',
      'transform:rotate(45deg)!important',
      'transform-origin:center!important',
      'margin-left:5px!important',
      'background:transparent!important',
      'opacity:1!important',
      'visibility:visible!important'
    ].join(';');
    btn.appendChild(arrow);

    btn.style.cssText = [
      'position:fixed!important',
      'top:122px!important',
      'right:14px!important',
      'left:auto!important',
      'z-index:1095!important',
      'display:flex!important',
      'align-items:center!important',
      'justify-content:center!important',
      'width:42px!important',
      'height:42px!important',
      'min-width:42px!important',
      'min-height:42px!important',
      'padding:0!important',
      'margin:0!important',
      'border:1px solid rgba(118,91,32,.30)!important',
      'border-radius:12px!important',
      'background:#f5f0e4!important',
      'box-shadow:0 3px 12px rgba(0,0,0,.08)!important',
      'appearance:none!important',
      '-webkit-appearance:none!important',
      'overflow:visible!important'
    ].join(';');
    btn.addEventListener('click', goBack);
    return btn;
  }

  function render() {
    const all = Array.from(document.querySelectorAll('#' + ID));
    let btn = all.shift() || null;
    all.forEach((node) => node.remove());
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

  const homeObserver = new MutationObserver(() => {
    if (document.querySelector('.wafd-role-home') || document.getElementById(ID)) {
      render();
    }
  });
  document.addEventListener('DOMContentLoaded', () => {
    if (document.body) homeObserver.observe(document.body, { childList: true, subtree: true });
  }, { once: true });
})();
