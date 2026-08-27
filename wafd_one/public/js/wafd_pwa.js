(function () {
  'use strict';
  const head = document.head || document.getElementsByTagName('head')[0];
  function ensureLink(rel, href, attrs={}) {
    let el = head.querySelector(`link[rel="${rel}"]`);
    if (!el) { el=document.createElement('link'); el.rel=rel; head.appendChild(el); }
    el.href=href; Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v)); return el;
  }
  function ensureMeta(name, content) {
    let el=head.querySelector(`meta[name="${name}"]`);
    if(!el){el=document.createElement('meta');el.name=name;head.appendChild(el)} el.content=content;
  }
  ensureLink('manifest','/assets/wafd_one/pwa/manifest.webmanifest',{crossorigin:'use-credentials'});
  ensureLink('apple-touch-icon','/assets/wafd_one/pwa/apple-touch-icon.png',{sizes:'180x180'});
  ensureMeta('theme-color','#18191d');
  ensureMeta('apple-mobile-web-app-capable','yes');
  ensureMeta('apple-mobile-web-app-status-bar-style','black-translucent');
  ensureMeta('apple-mobile-web-app-title','WAFD ONE');
  ensureMeta('mobile-web-app-capable','yes');
  ensureMeta('format-detection','telephone=no');

  window.wafdIsStandalone = !!(
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  );

  // Keep install UX fully native. Do not call preventDefault() on
  // beforeinstallprompt unless WAFD ONE provides its own install button.
  // Android/Chromium can therefore expose the browser's normal Install UI.
  // iOS/iPadOS uses Share > Add to Home Screen / Open as Web App.
})();
