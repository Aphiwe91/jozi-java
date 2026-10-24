/* Coffee collection: instant search, URL search and stable sorting. */
(function () {
  'use strict';
  var grid = document.getElementById('jj-grid');
  if (!grid) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.jj-card-wrap'));
  var search = document.getElementById('jj-shop-search');
  var sort = document.getElementById('jj-sort');
  var params = new URLSearchParams(window.location.search);
  search.value = (params.get('q') || '').slice(0, 100).trim();
  function update() {
    var query = search.value.trim().toLocaleLowerCase();
    var words = query.split(/\s+/).filter(Boolean);
    var shown = 0;
    var ordered = cards.slice();
    if (sort.value === 'name') ordered.sort(function (a, b) { return a.dataset.name.localeCompare(b.dataset.name); });
    else if (sort.value === 'price-asc') ordered.sort(function (a, b) { return Number(a.dataset.price) - Number(b.dataset.price); });
    else if (sort.value === 'price-desc') ordered.sort(function (a, b) { return Number(b.dataset.price) - Number(a.dataset.price); });
    else ordered.sort(function (a, b) { return Number(a.dataset.featured) - Number(b.dataset.featured); });
    ordered.forEach(function (card) {
      var text = card.textContent.toLocaleLowerCase();
      card.hidden = !words.every(function (word) { return text.indexOf(word) !== -1; });
      if (!card.hidden) shown++;
      grid.appendChild(card);
    });
    document.querySelector('.jj-collection-count').textContent = query
      ? shown + (shown === 1 ? ' roast' : ' roasts') + ' matching “' + search.value.trim() + '”'
      : '3 roasts · 9 bag options';
    document.getElementById('jj-search-empty').hidden = shown !== 0;
    document.querySelectorAll('.jj-nav-search input').forEach(function (input) { input.value = search.value; });
    var url = new URL(window.location.href);
    if (search.value.trim()) url.searchParams.set('q', search.value.trim()); else url.searchParams.delete('q');
    try { history.replaceState(null, '', url.pathname + url.search + url.hash); } catch (error) { /* file: preview still filters */ }
  }
  search.addEventListener('input', update); sort.addEventListener('change', update);
  document.getElementById('jj-clear-search').addEventListener('click', function () { search.value = ''; update(); search.focus(); });
  update();
})();
