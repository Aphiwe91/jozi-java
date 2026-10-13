/* Jozi Java shop page: collection sort bar + size pills.
   Presentation only — no cart integration (Add to Cart still links to cart.html). */
(function () {
  'use strict';

  function fmt(n) { return 'R' + n.toFixed(2); }

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

    /* Size pills: picking a size swaps the card price; re-click clears back to "from" */
    grid.addEventListener('click', function (e) {
      var btn = e.target.closest ? e.target.closest('.jj-size') : null;
      if (!btn) return;
      var group = btn.parentNode;
      var card = group.closest('.jj-card');
      var priceEl = card.querySelector('.jj-price span');
      var prices = JSON.parse(group.getAttribute('data-prices'));
      var wasActive = btn.classList.contains('active');
      Array.prototype.forEach.call(group.querySelectorAll('.jj-size'), function (b) {
        b.classList.remove('active');
      });
      if (wasActive) {
        var min = Math.min.apply(null, Object.keys(prices).map(function (k) { return prices[k]; }));
        priceEl.textContent = 'from ' + fmt(min);
      } else {
        btn.classList.add('active');
        priceEl.textContent = fmt(prices[btn.textContent.trim()]);
      }
    });
  });
})();
