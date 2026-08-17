(function () {
  const HOME = '/desk/wafd-role-home';

  function isMobile() { return window.matchMedia('(max-width: 767px)').matches; }
  function isHome() {
    const path = window.location.pathname.replace(/\/$/, '');
    return path === HOME || path === '/app/wafd-role-home' || path === '/wafd-mobile';
  }
  function goBack() {
    if (window.history.length > 1) window.history.back();
    else window.location.assign(HOME);
  }
  function renderBackButton() {
    const old = document.getElementById('wafd-global-mobile-back');
    if (!isMobile() || isHome()) { if (old) old.remove(); return; }
    if (old) return;
    const btn = document.createElement('button');
    btn.id = 'wafd-global-mobile-back';
    btn.type = 'button';
    btn.className = 'btn btn-default wafd-global-mobile-back';
    btn.setAttribute('aria-label', 'رجوع');
    btn.innerHTML = '<span aria-hidden="true">‹</span><span>رجوع</span>';
    btn.addEventListener('click', goBack);
    document.body.appendChild(btn);
  }

  document.addEventListener('DOMContentLoaded', renderBackButton);
  window.addEventListener('popstate', () => setTimeout(renderBackButton, 50));
  window.addEventListener('resize', renderBackButton);
  if (window.frappe?.router?.on) frappe.router.on('change', () => setTimeout(renderBackButton, 80));
  setTimeout(renderBackButton, 250);
})();
