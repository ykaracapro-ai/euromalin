/* ============================================================
   EuroMalin — Theme toggle
   - Respecte prefers-color-scheme par défaut
   - Permet override manuel via data-theme + localStorage
   - À placer en haut du <body> ou idéalement en <head>
     (inline, voir snippet anti-flash plus bas)
   ============================================================ */

(function () {
  const STORAGE_KEY = 'euromalin-theme';
  const root = document.documentElement;

  // Applique le thème stocké si présent (override manuel)
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') {
    root.setAttribute('data-theme', stored);
  }

  // Branche le bouton (si présent)
  function bindToggle() {
    const btn = document.querySelector('[data-theme-toggle]');
    if (!btn) return;

    btn.addEventListener('click', () => {
      const current =
        root.getAttribute('data-theme') ||
        (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      const next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch (e) {}
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindToggle);
  } else {
    bindToggle();
  }

  // Toggle mobile nav (bonus)
  function bindNav() {
    const navBtn = document.querySelector('[data-nav-toggle]');
    const navLinks = document.querySelector('.nav-links');
    if (!navBtn || !navLinks) return;
    navBtn.addEventListener('click', () => {
      navLinks.classList.toggle('is-open');
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindNav);
  } else {
    bindNav();
  }
})();
