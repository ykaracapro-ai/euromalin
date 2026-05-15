(function () {
  'use strict';

  /* Anti-flash: apply stored theme as early as possible */
  try {
    var saved = localStorage.getItem('euromalin-theme');
    if (saved === 'dark' || saved === 'light') {
      document.documentElement.setAttribute('data-theme', saved);
    }
  } catch (e) {}

  document.addEventListener('DOMContentLoaded', function () {
    enhanceLegacyHeader();
    initNavToggle();
    initThemeToggle();
    initSearch();
    initActiveNav();
    initReveal();
    initScrollProgress();
  });

  /* ----- Inject nav-toggle + theme-toggle into legacy .topbar headers ----- */
  function enhanceLegacyHeader() {
    var topbar = document.querySelector('.topbar');
    if (!topbar) return; // modern .site-header already has both
    var nav = topbar.querySelector('.container.nav') || topbar.querySelector('.nav');
    if (!nav) return;

    // If already has actions/toggles, do nothing
    if (nav.querySelector('.nav-actions, [data-nav-toggle], [data-theme-toggle]')) return;

    var actions = document.createElement('div');
    actions.className = 'nav-actions';

    // Existing CTA button (Voir les articles) — move it inside .nav-actions if present
    var existingBtn = Array.from(nav.children).find(function (el) {
      return el.tagName === 'A' && el.classList.contains('btn');
    });

    actions.innerHTML = [
      '<button class="theme-toggle" data-theme-toggle aria-label="Changer de thème" type="button">',
      '  <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
      '  <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>',
      '</button>',
      '<button class="nav-toggle" data-nav-toggle aria-label="Menu" aria-expanded="false" type="button">',
      '  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 12h18M3 6h18M3 18h18"/></svg>',
      '</button>'
    ].join('');

    if (existingBtn) actions.insertBefore(existingBtn, actions.firstChild);
    nav.appendChild(actions);
  }

  /* ----- Mobile nav toggle ----- */
  function initNavToggle() {
    var btn = document.querySelector('[data-nav-toggle], .nav-toggle');
    var links = document.querySelector('.nav-links');
    if (!btn || !links) return;
    btn.setAttribute('aria-expanded', 'false');
    btn.addEventListener('click', function () {
      var open = links.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    links.addEventListener('click', function (e) {
      if (e.target && e.target.tagName === 'A') {
        links.classList.remove('is-open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('is-open')) {
        links.classList.remove('is-open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 900 && links.classList.contains('is-open')) {
        links.classList.remove('is-open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ----- Theme toggle (light/dark) ----- */
  function initThemeToggle() {
    var btn = document.querySelector('[data-theme-toggle], .theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-theme');
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      var next;
      if (current === 'dark') next = 'light';
      else if (current === 'light') next = 'dark';
      else next = prefersDark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('euromalin-theme', next); } catch (e) {}
    });
  }

  /* ----- Article search ----- */
  function initSearch() {
    var search = document.querySelector('[data-search], .search-wrap .search, .search input, input[type="search"]');
    if (!search) return;
    var cards = Array.from(document.querySelectorAll('[data-article-card], .article-card'));
    if (!cards.length) return;
    var empty = document.querySelector('[data-no-results]');
    var run = debounce(function () {
      var q = search.value.trim().toLowerCase();
      var visible = 0;
      cards.forEach(function (card) {
        var text = (card.textContent || '').toLowerCase();
        var match = !q || text.indexOf(q) !== -1;
        card.style.display = match ? '' : 'none';
        if (match) visible++;
      });
      if (empty) empty.style.display = visible === 0 ? 'block' : 'none';
    }, 80);
    search.addEventListener('input', run);
  }

  function debounce(fn, wait) {
    var t;
    return function () {
      var ctx = this, args = arguments;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, wait);
    };
  }

  /* ----- Active nav link ----- */
  function initActiveNav() {
    var path = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    if (location.pathname.indexOf('/articles/') !== -1) path = 'articles.html';
    if (location.pathname.indexOf('/bons-plans/') !== -1) path = 'bons-plans.html';
    document.querySelectorAll('.nav-links a').forEach(function (a) {
      var href = (a.getAttribute('href') || '').split('/').pop().toLowerCase();
      if (href && href === path) a.setAttribute('aria-current', 'page');
    });
  }

  /* ----- Reveal on scroll ----- */
  function initReveal() {
    var els = document.querySelectorAll('.reveal');
    if (!els.length || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -40px 0px', threshold: 0.05 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ----- Scroll progress for article pages ----- */
  function initScrollProgress() {
    var bar = document.querySelector('[data-scroll-progress], .scroll-progress');
    if (!bar) {
      // Auto-create for article pages
      if (!document.querySelector('article.article, .article.hero-card')) return;
      bar = document.createElement('div');
      bar.className = 'scroll-progress';
      document.body.insertBefore(bar, document.body.firstChild);
    }
    var ticking = false;
    function update() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      var pct = max > 0 ? (h.scrollTop / max) * 100 : 0;
      bar.style.width = pct + '%';
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  }
})();
