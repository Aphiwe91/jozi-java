/* Jozi Java shop page: collection sort bar.
   Size pills, grind select and Add to Cart live in js/cart.js (single source of truth
   for prices so the cart always matches what the card shows). */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var grid = document.getElementById('jj-grid');
    if (!grid) return;
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.jj-card-wrap'));

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
