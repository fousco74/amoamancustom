/**
 * Stockage & API globale – window.CookieConsent
 *
 * Extrait de templates/layout.html (où il était en ligne) pour être partagé par
 * les deux gabarits du site : layout.html (corporate) et layout_erpnext.html
 * (mini-site /erpnext). La clé `cookie_prefs_v1` et l'origine étant les mêmes,
 * un choix fait sur /cookies vaut pour /erpnext/cookies et inversement.
 *
 * Ce fichier ne contient QUE l'API de stockage. La bannière de consentement
 * reste dans layout.html : le mini-site n'en affiche pas, puisqu'il ne charge
 * aucun traceur (ni Matomo ni autre) soumis à consentement.
 *
 * Chargé en <script> classique, AVANT tout script qui lit window.CookieConsent
 * (la bannière de layout.html, includes/legal/cookies_preferences.html).
 */
(function () {
  'use strict';
  const KEY = 'cookie_prefs_v1';

  function _supportsLS() {
    try {
      if (typeof localStorage === 'undefined') return false;
      localStorage.setItem('__t', '1');
      localStorage.removeItem('__t');
      return true;
    } catch (e) { return false; }
  }

  function _read() {
    if (typeof document === 'undefined') return null;
    if (_supportsLS()) {
      const raw = localStorage.getItem(KEY);
      if (!raw) return null;
      try { return JSON.parse(raw); } catch { return null; }
    } else {
      const m = document.cookie.match(new RegExp('(^| )' + KEY + '=([^;]+)'));
      return m ? JSON.parse(decodeURIComponent(m[2])) : null;
    }
  }

  function _write(prefs) {
    const payload = JSON.stringify(prefs);
    if (_supportsLS()) {
      localStorage.setItem(KEY, payload);
    } else {
      const exp = new Date();
      exp.setFullYear(exp.getFullYear() + 1);
      document.cookie = KEY + '=' + encodeURIComponent(payload) + ';expires=' + exp.toUTCString() + ';path=/';
    }
    if (typeof document !== 'undefined' && typeof CustomEvent !== 'undefined') {
      document.dispatchEvent(new CustomEvent('consent:applied', { detail: prefs }));
    }
  }

  window.CookieConsent = {
    get() { return _read(); },
    set(p) {
      const prefs = Object.assign(
        { necessary: true, analytics: false, functional: false, marketing: false },
        p,
        { ts: Date.now() }
      );
      _write(prefs);
      return prefs;
    },
    acceptAll() { return this.set({ necessary: true, analytics: true, functional: true, marketing: true }); },
    rejectAll() { return this.set({ necessary: true, analytics: false, functional: false, marketing: false }); }
  };
})();
