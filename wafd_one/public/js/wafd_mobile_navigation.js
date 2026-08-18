(function () {
  const HOME = '/desk/wafd-role-home';
  const ID = 'wafd-global-mobile-back';
  function isMobile(){ return window.matchMedia('(max-width: 767px)').matches; }
  function route(){ try { return window.frappe?.get_route?.() || []; } catch(e){ return []; } }
  function isHome(){
    const p=location.pathname.replace(/\/$/,'');
    return p===HOME || p==='/app/wafd-role-home' || p==='/wafd-mobile' || (route()[0]==='wafd-role-home');
  }
  function goBack(){
    // Prefer Frappe/browser history so iOS swipe and the icon behave identically.
    if (history.length > 1) { history.back(); return; }
    if (window.frappe?.set_route) { frappe.set_route('wafd-role-home'); return; }
    location.assign(HOME);
  }
  function createButton(){
    const btn=document.createElement('button');
    btn.id=ID; btn.type='button'; btn.className='wafd-global-mobile-back';
    btn.setAttribute('aria-label','رجوع'); btn.setAttribute('title','رجوع');
    btn.innerHTML='<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    btn.addEventListener('click',goBack);
    return btn;
  }
  function render(){
    let btn=document.getElementById(ID);
    if(!isMobile() || isHome()){ if(btn) btn.remove(); return; }
    if(!btn) btn=createButton();
    // Keep it in the native navbar action area; do not float over forms/buttons.
    const host=document.querySelector('.navbar .navbar-right, .navbar .nav, header .navbar-right, .navbar');
    if(host && btn.parentElement!==host) host.prepend(btn);
  }
  document.addEventListener('DOMContentLoaded',()=>setTimeout(render,60));
  addEventListener('popstate',()=>setTimeout(render,60));
  addEventListener('resize',render);
  if(window.frappe?.router?.on) frappe.router.on('change',()=>setTimeout(render,80));
  setTimeout(render,250);
})();
