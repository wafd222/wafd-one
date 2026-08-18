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
    const host = document.querySelector('.page-body') || document.querySelector('#body') || document.body;
    if (btn.parentElement !== host) host.appendChild(btn);
  }

  document.addEventListener('DOMContentLoaded', () => setTimeout(render, 60));
  window.addEventListener('popstate', () => setTimeout(render, 60));
  window.addEventListener('resize', render);
  if (window.frappe?.router?.on) frappe.router.on('change', () => setTimeout(render, 80));
  setTimeout(render, 250);
})();
