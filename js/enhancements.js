(function ($) {
  'use strict';

  function ready(fn) { if (document.readyState !== 'loading') { fn(); } else { document.addEventListener('DOMContentLoaded', fn); } }

  // ---------- sticky glass navbar ----------
  function navOnScroll() {
    var nav = document.querySelector('.ftco_navbar');
    if (!nav) return;
    function update() { nav.classList.toggle('scrolled', (window.scrollY || window.pageYOffset) > 60); }
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  // ---------- reveal on scroll ----------
  function setupReveal() {
    var targets = document.querySelectorAll('.ftco-section .heading-section, .menu-entry, .block-6, .testimony, .jj-cta, #ftco-about .one-half');
    targets.forEach(function (el) { el.classList.add('reveal-up'); });
    if (!('IntersectionObserver' in window)) { targets.forEach(function (el) { el.classList.add('in'); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var delay = Number(el.dataset.delay || 0);
        setTimeout(function () { el.classList.add('in'); }, delay);
        io.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    targets.forEach(function (el, i) { el.dataset.delay = (i % 6) * 70; io.observe(el); });
  }

  // ---------- animated counters ----------
  function animateCounters() {
    var nums = document.querySelectorAll('#section-counter .number');
    if (!nums.length || !('IntersectionObserver' in window)) return;
    var seen = false;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting && !seen) { seen = true; run(); } });
    }, { threshold: 0.4 });
    nums.forEach(function (n) { io.observe(n); });
    function run() {
      nums.forEach(function (n) {
        var target = parseFloat(n.getAttribute('data-number'));
        var isPct = n.nextSibling && (n.nextSibling.textContent || '').trim().match(/%/);
        var duration = 1600, start = null;
        function frame(ts) { if (!start) start = ts; var prog = Math.min(1, (ts - start) / duration); var val = Math.round(target * (0.5 - 0.5 * Math.cos(Math.PI * prog))); n.textContent = val; if (prog < 1) requestAnimationFrame(frame); }
        requestAnimationFrame(frame);
      });
    }
  }

  // ---------- floating WhatsApp + back-to-top ----------
  function injectFab() {
    if (document.querySelector('.jj-fab--wa')) return;
    var wa = document.createElement('a');
    wa.className = 'jj-fab jj-fab--wa'; wa.href = 'https://wa.me/c/27689235818'; wa.target = '_blank'; wa.rel = 'noopener'; wa.setAttribute('aria-label', 'Chat on WhatsApp');
    wa.innerHTML = '<svg viewBox="0 0 24 24"><path d="M17.49 14.38c-.3-.15-1.77-.87-2.04-.97-.28-.1-.49-.15-.69.15-.21.3-.8.97-.98 1.17-.18.2-.36.22-.66.08-.3-.15-1.26-.46-2.4-1.48-.89-.79-1.49-1.77-1.66-2.07-.18-.3-.02-.46.13-.6.13-.13.3-.34.44-.51.15-.18.2-.3.3-.49.1-.2.05-.37-.02-.52-.08-.15-.69-1.66-.94-2.28-.25-.6-.5-.52-.69-.53-.18-.01-.38-.01-.6-.01-.2 0-.52.07-.79.37-.28.3-1.04 1.02-1.04 2.49s1.06 2.9 1.21 3.1c.15.2 2.08 3.17 5.03 4.44.7.3 1.25.48 1.68.62.7.22 1.34.19 1.85.12.56-.08 1.77-.72 2.02-1.41.24-.7.24-1.3.17-1.41-.08-.13-.28-.2-.58-.35zM12 2C6.48 2 2 6.48 2 12c0 1.82.49 3.53 1.33 4.99L2 22l5.13-1.33C8.53 21.49 10.22 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2z"/></svg>';
    document.body.appendChild(wa);

    var up = document.createElement('a');
    up.className = 'jj-fab jj-fab--up'; up.href = '#'; up.setAttribute('aria-label', 'Back to top');
    up.innerHTML = '<svg viewBox="0 0 24 24"><path d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z"/></svg>';
    up.addEventListener('click', function (e) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
    document.body.appendChild(up);
    function toggleUp() { up.classList.toggle('is-visible', (window.scrollY || 0) > 400); }
    window.addEventListener('scroll', toggleUp, { passive: true });
    toggleUp();
  }

  // ---------- smooth anchor scroll ----------
  function smoothAnchors() {
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(function (a) {
      a.addEventListener('click', function (e) {
        var t = document.querySelector(a.getAttribute('href'));
        if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
      });
    });
  }

  // ---------- equipment filter ----------
  function equipFilter() {
    var input = document.getElementById('equipSearch');
    if (!input) return;
    input.addEventListener('input', function () {
      var q = (input.value || '').toLowerCase().trim();
      document.querySelectorAll('.jj-table tbody tr').forEach(function (tr) {
        if (!tr.closest('#equipSearch')) {
          tr.style.display = (q === '' || tr.textContent.toLowerCase().indexOf(q) > -1) ? '' : 'none';
        }
      });
    });
  }

  // ---------- theme animate safety net ----------
  /* The Colorlib theme hides every `.ftco-animate` block (opacity 0 + visibility hidden)
     and relied on a jQuery waypoint to fade it in. Any block that was already on screen
     when the page loaded — or reached by a jump link / scrolling back up — stayed
     invisible (that is why the bottom CONTACT US form could be missing). Reveal anything
     the visitor can see; blocks still below the fold keep their entrance animation. */
  function animateFailsafe() {
    var pending = document.querySelectorAll('.ftco-animate:not(.ftco-animated)');
    if (!pending.length) return;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    for (var i = 0; i < pending.length; i++) {
      var el = pending[i];
      if (el.getBoundingClientRect().top >= vh) continue; // still below the fold
      var effect = el.getAttribute('data-animate-effect');
      if (effect !== 'fadeIn' && effect !== 'fadeInLeft' && effect !== 'fadeInRight') effect = 'fadeInUp';
      el.classList.add(effect, 'ftco-animated');
      el.classList.remove('item-animate');
    }
  }

  function watchAnimateFailsafe() {
    var queued = false;
    function tick() { queued = false; animateFailsafe(); }
    function onScroll() { if (!queued) { queued = true; setTimeout(tick, 60); } }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    window.addEventListener('load', animateFailsafe);
    animateFailsafe();
  }

  ready(function () {
    navOnScroll();
    setupReveal();
    animateCounters();
    equipFilter();
    injectFab();
    smoothAnchors();
    watchAnimateFailsafe();
  });
})(window.jQuery || (function ($) { return $; }));
