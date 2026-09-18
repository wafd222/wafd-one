(function () {
  'use strict';

  // RC212: iOS Safari exposes short UI notification sounds as a system media
  // session, which leaves a player card on the lock screen. WAFD ONE does not
  // require audio for any operational workflow, so silence app audio on iOS
  // while preserving all visual notifications and document actions.
  const ua = navigator.userAgent || '';
  const platform = navigator.platform || '';
  const isIOS = /iPad|iPhone|iPod/.test(ua) ||
    (platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  if (!isIOS) return;

  const resolved = () => Promise.resolve();

  function clearMediaSession() {
    if (!('mediaSession' in navigator)) return;
    try { navigator.mediaSession.metadata = null; } catch (_e) {}
    try { navigator.mediaSession.playbackState = 'none'; } catch (_e) {}
    const actions = [
      'play', 'pause', 'stop', 'seekbackward', 'seekforward',
      'seekto', 'previoustrack', 'nexttrack'
    ];
    actions.forEach((action) => {
      try { navigator.mediaSession.setActionHandler(action, null); } catch (_e) {}
    });
  }

  function silenceElement(el) {
    if (!el || String(el.tagName).toUpperCase() !== 'AUDIO') return;
    try { el.muted = true; } catch (_e) {}
    try { el.volume = 0; } catch (_e) {}
    try { el.pause(); } catch (_e) {}
    try { el.currentTime = 0; } catch (_e) {}
  }

  // Block HTMLAudioElement playback before Safari can create a Now Playing
  // session. Video playback is deliberately untouched.
  if (window.HTMLMediaElement && !window.HTMLMediaElement.prototype.__wafdIOSAudioSilenced) {
    const nativePlay = window.HTMLMediaElement.prototype.play;
    window.HTMLMediaElement.prototype.play = function () {
      if (String(this.tagName).toUpperCase() === 'AUDIO') {
        silenceElement(this);
        clearMediaSession();
        return resolved();
      }
      return nativePlay.apply(this, arguments);
    };
    Object.defineProperty(window.HTMLMediaElement.prototype, '__wafdIOSAudioSilenced', {
      value: true,
      configurable: false,
      enumerable: false,
      writable: false,
    });
  }

  function disableFrappeSounds() {
    try {
      if (window.frappe) {
        if (frappe.utils && typeof frappe.utils.play_sound === 'function') {
          frappe.utils.play_sound = function () { clearMediaSession(); return resolved(); };
        }
        if (typeof frappe.play_sound === 'function') {
          frappe.play_sound = function () { clearMediaSession(); return resolved(); };
        }
      }
    } catch (_e) {}
  }

  function sweepAudio() {
    try { document.querySelectorAll('audio').forEach(silenceElement); } catch (_e) {}
    clearMediaSession();
    disableFrappeSounds();
  }

  document.addEventListener('DOMContentLoaded', sweepAudio, { once: true });
  window.addEventListener('pageshow', sweepAudio);
  window.addEventListener('focus', sweepAudio);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') sweepAudio();
  });

  // Catch audio elements inserted later by Frappe notifications.
  const startObserver = () => {
    if (!document.documentElement || !window.MutationObserver) return;
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (!node || node.nodeType !== 1) return;
          if (String(node.tagName).toUpperCase() === 'AUDIO') silenceElement(node);
          try { node.querySelectorAll?.('audio').forEach(silenceElement); } catch (_e) {}
        });
      });
      clearMediaSession();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startObserver, { once: true });
  } else {
    startObserver();
  }

  // Frappe may attach its helper after this app bundle executes; re-apply a
  // few times during boot without keeping a permanent interval alive.
  [0, 150, 500, 1200, 2500, 5000].forEach((delay) => setTimeout(sweepAudio, delay));
})();
