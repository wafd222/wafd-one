(function () {
  const HOME = '/desk/wafd-role-home';
  function isMobile(){ return window.matchMedia('(max-width: 767px)').matches; }
  function isHome(){ const p=location.pathname.replace(/\/$/,''); return p===HOME||p==='/app/wafd-role-home'||p==='/wafd-mobile'; }
  function goBack(){
    try {
      if (window.frappe?.get_route && frappe.get_route().length && history.length > 1) { history.back(); return; }
    } catch(e) {}
    location.assign(HOME);
  }
  function renderBackButton(){
    let btn=document.getElementById('wafd-global-mobile-back');
    if(!isMobile()||isHome()){ if(btn)btn.remove(); return; }
    if(!btn){
      btn=document.createElement('button'); btn.id='wafd-global-mobile-back'; btn.type='button';
      btn.className='btn btn-default wafd-global-mobile-back'; btn.setAttribute('aria-label','رجوع');
      btn.innerHTML='<span aria-hidden="true">‹</span><span>رجوع</span>'; btn.addEventListener('click',goBack);
    }
    const host=document.querySelector('.navbar .container, .navbar, header .container, header');
    if(host && btn.parentElement!==host) host.appendChild(btn); else if(!host && !btn.parentElement) document.body.appendChild(btn);
  }
  document.addEventListener('DOMContentLoaded',renderBackButton);
  addEventListener('popstate',()=>setTimeout(renderBackButton,50)); addEventListener('resize',renderBackButton);
  if(window.frappe?.router?.on) frappe.router.on('change',()=>setTimeout(renderBackButton,80));
  setTimeout(renderBackButton,250);
})();