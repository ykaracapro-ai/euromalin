(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    initNavToggle();
    initThemeToggle();
    initSearch();
    initActiveNav();
    initReveal();
    initScrollProgress();
  });

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
      if (window.innerWidth > 800 && links.classList.contains('is-open')) {
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
    var search = document.querySelector('[data-search], .search input, input[type="search"]');
    if (!search) return;
    var cards = Array.from(document.querySelectorAll('[data-article-card]'));
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
      if (empty) empty.style.display = visible === 0 ? '' : 'none';
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
    if (!bar) return;
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
