(function () {
  'use strict';

  /* Theme: load saved preference */
  try {
    var savedTheme = localStorage.getItem('euromalin-theme');
    if (savedTheme === 'dark' || savedTheme === 'light') {
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  } catch (e) {}

  document.addEventListener('DOMContentLoaded', function () {
    initNavToggle();
    initThemeToggle();
    initSearch();
    initScrollProgress();
    initReveal();
    initActiveNav();
  });

  /* Mobile nav toggle */
  function initNavToggle() {
    var btn = document.querySelector('[data-nav-toggle]');
    var drawer = document.querySelector('[data-nav-drawer]');
    if (!btn || !drawer) return;
    btn.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    });
    drawer.addEventListener('click', function (e) {
      if (e.target && e.target.tagName === 'A') closeNav(btn);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && document.body.classList.contains('nav-open')) closeNav(btn);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth >= 880 && document.body.classList.contains('nav-open')) closeNav(btn);
    });
  }

  function closeNav(btn) {
    document.body.classList.remove('nav-open');
    document.body.style.overflow = '';
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }

  /* Theme toggle */
  function initThemeToggle() {
    var btn = document.querySelector('[data-theme-toggle]');
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

  /* Article search filter */
  function initSearch() {
    var search = document.querySelector('[data-search]');
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
      if (empty) empty.classList.toggle('is-visible', visible === 0);
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

  /* Scroll progress bar for article pages */
  function initScrollProgress() {
    var bar = document.querySelector('[data-scroll-progress]');
    if (!bar) return;
    var ticking = false;
    function update() {
      var h = document.documentElement;
      var scrolled = h.scrollTop;
      var max = h.scrollHeight - h.clientHeight;
      var pct = max > 0 ? (scrolled / max) * 100 : 0;
      bar.style.width = pct + '%';
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  }

  /* Reveal on scroll */
  function initReveal() {
    var els = document.querySelectorAll('.reveal, .card, .article-card, .offer, .stat');
    if (!els.length || !('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    els.forEach(function (el) { el.classList.add('reveal'); });
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

  /* Highlight active nav link */
  function initActiveNav() {
    var path = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    if (location.pathname.indexOf('/articles/') !== -1) path = 'articles.html';
    document.querySelectorAll('.nav-links a, .nav-drawer a').forEach(function (a) {
      var href = (a.getAttribute('href') || '').split('/').pop().toLowerCase();
      if (href === path) a.classList.add('is-active');
    });
  }
})();
