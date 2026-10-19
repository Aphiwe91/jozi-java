/* Jozi Java shop page: collection sort bar.
   Size pills, grind select and Add to Cart live in js/cart.js (single source of truth
   for prices so the cart always matches what the card shows). */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var grid = document.getElementById('jj-grid');
    if (!grid) return;
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.jj-card-wrap'));

    /* Nav search (?q=…): keep only the roasts whose card text matches, and say so in the bar */
    var term = '';
    try { term = (new URLSearchParams(window.location.search).get('q') || '').trim(); } catch (e) { term = ''; }
    if (term) {
      /* keep the nav search box showing what is being filtered */
      Array.prototype.forEach.call(document.querySelectorAll('.jj-nav-search input'), function (input) {
        if (!input.value) { input.value = term; }
      });
      var needle = term.toLowerCase();
      var shown = 0;
      cards.forEach(function (card) {
        var hit = (card.textContent || '').toLowerCase().indexOf(needle) !== -1;
        (card.closest('.col') || card).hidden = !hit;
        if (hit) { shown++; }
      });
      var bar = document.querySelector('.jj-collection-bar');
      var count = document.querySelector('.jj-collection-count');
      if (count) {
        count.textContent = shown
          ? shown + (shown === 1 ? ' roast' : ' roasts') + ' matching \u201c' + term + '\u201d'
          : 'No roasts matching \u201c' + term + '\u201d';
      }
      if (bar) {
        var clear = document.createElement('a');
        clear.className = 'jj-search-clear';
        clear.href = 'shop.html';
        clear.textContent = 'Clear search';
        bar.appendChild(clear);
      }
    }

    /* Sort bar (Featured / price / A-Z), Truth Coffee-style */
    var sort = document.getElementById('jj-sort');
    if (sort) {
      sort.addEventListener('change', function () {
        var mode = sort.value;
        var ordered = cards.slice();
        if (mode === 'price-asc') {
          ordered.sort(function (a, b) { return parseFloat(a.dataset.price) - parseFloat(b.dataset.price); });
        } else if (mode === 'price-desc') {
          ordered.sort(function (a, b) { return parseFloat(b.dataset.price) - parseFloat(a.dataset.price); });
        } else if (mode === 'name') {
          ordered.sort(function (a, b) { return a.dataset.name.localeCompare(b.dataset.name); });
        } else {
          ordered.sort(function (a, b) { return parseFloat(a.dataset.featured) - parseFloat(b.dataset.featured); });
        }
        ordered.forEach(function (card) { grid.appendChild(card); });
      });
    }
  });
})();
