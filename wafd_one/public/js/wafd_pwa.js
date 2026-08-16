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

  // Keep install UX native. Android/Chromium will expose Install when the browser deems the app installable.
  // iOS uses Share > Add to Home Screen; the Apple meta/icon above make it open as a standalone app.
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    window.wafdPwaInstallPrompt = event;
    window.dispatchEvent(new CustomEvent('wafd:pwa-install-ready'));
  });
})();
