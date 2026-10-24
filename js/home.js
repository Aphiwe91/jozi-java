/* Accessible, dependency-free 10-second home and category carousels.
   Pause on focus/hover, in background tabs and for reduced-motion preferences. */
(function () {
  'use strict';
  var hero = document.querySelector('.jj-home-hero');
  if (!hero) return;
  var slides = Array.prototype.slice.call(hero.querySelectorAll('.jj-hero-slide'));
  var controls = hero.querySelector('.jj-hero-dots');
  var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var paused = motion.matches, hovered = false, focused = false, index = 0, timer;
  var tiles = Array.prototype.slice.call(document.querySelectorAll('.jj-tile')).map(function (tile) { return { el: tile, slides: tile.querySelectorAll('img'), index: 0 }; });
  var typingFinish = function () {};

  function show(next) {
    index = (next + slides.length) % slides.length;
    slides.forEach(function (slide, i) {
      var active = i === index;
      slide.classList.toggle('is-active', active); slide.setAttribute('aria-hidden', String(!active)); slide.inert = !active;
      controls.children[i].setAttribute('aria-pressed', String(active));
    });
    hero.querySelector('.jj-slide-count').textContent = '0' + (index + 1) + ' / 0' + slides.length;
  }
  function schedule() {
    clearInterval(timer);
    if (paused || hovered || focused || document.hidden) return;
    timer = setInterval(function () {
      show(index + 1);
      tiles.forEach(function (tile) {
        if (tile.el.matches(':hover,:focus-within') || tile.slides.length < 2) return;
        tile.slides[tile.index].classList.remove('is-active');
        tile.index = (tile.index + 1) % tile.slides.length;
        tile.slides[tile.index].classList.add('is-active');
      });
    }, 10000);
  }
  slides.forEach(function (slide, i) {
    var button = document.createElement('button'); button.type = 'button';
    button.setAttribute('aria-label', 'Show slide ' + (i + 1)); button.setAttribute('aria-pressed', String(i === 0));
    button.addEventListener('click', function () { show(i); schedule(); }); controls.appendChild(button);
  });
  hero.querySelector('.jj-slide-prev').addEventListener('click', function () { show(index - 1); schedule(); });
  hero.querySelector('.jj-slide-next').addEventListener('click', function () { show(index + 1); schedule(); });
  var toggle = hero.querySelector('.jj-motion-toggle');
  function syncToggle() { toggle.textContent = paused ? 'Resume motion' : 'Pause motion'; toggle.setAttribute('aria-pressed', String(paused)); }
  toggle.addEventListener('click', function () { paused = !paused; if (paused) typingFinish(); syncToggle(); schedule(); });
  hero.addEventListener('mouseenter', function () { hovered = true; schedule(); });
  hero.addEventListener('mouseleave', function () { hovered = false; schedule(); });
  hero.addEventListener('focusin', function () { focused = true; schedule(); });
  hero.addEventListener('focusout', function (event) { if (!hero.contains(event.relatedTarget)) { focused = false; schedule(); } });
  document.addEventListener('visibilitychange', schedule);
  motion.addEventListener('change', function () { paused = motion.matches; if (paused) typingFinish(); syncToggle(); schedule(); });
  syncToggle(); show(0); schedule();

  /* Keep the complete story in the accessible tree and reserve its full height.
     Typing is decorative, runs once, and never erases or reflows the section. */
  var story = document.getElementById('story-typing');
  if (story && !motion.matches && 'IntersectionObserver' in window) {
    var fullText = story.textContent, full = document.createElement('span'), typed = document.createElement('span');
    var typingTimer, cursor = 0, started = false;
    full.className = 'jj-story-full'; full.textContent = fullText;
    typed.className = 'jj-story-typed'; typed.setAttribute('aria-hidden', 'true');
    story.replaceChildren(full, typed);
    typingFinish = function () { clearTimeout(typingTimer); typed.textContent = fullText; typed.classList.add('is-complete'); cursor = fullText.length; };
    function type() {
      if (paused) { typingFinish(); return; }
      cursor = Math.min(cursor + 3, fullText.length); typed.textContent = fullText.slice(0, cursor);
      if (cursor < fullText.length) typingTimer = setTimeout(type, 22); else typed.classList.add('is-complete');
    }
    var observer = new IntersectionObserver(function (entries) {
      if (entries.some(function (entry) { return entry.isIntersecting; }) && !started) { started = true; observer.disconnect(); type(); }
    }, { threshold: 0.15 });
    observer.observe(story);
  }
})();
