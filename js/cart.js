/* Jozi Java cart — localStorage cart + WhatsApp order handoff.
   Presentation + local state only. No payment gateway yet: the brief (section 12) plans
   Shopify/PayFast longer-term, so today an order is handed to WhatsApp Business
   (wa.me/27689235818) with the lines, totals and customer details pre-filled.

   Pages it drives:
     - every page  : nav cart link + live count badge, toasts
     - shop.html   : size pills + grind select + "Add to Cart" on .jj-card
     - cart.html   : line table, qty steppers, remove, totals
     - checkout.html: order summary, delivery method, validation, WhatsApp handoff

   Marked PLACEHOLDER below: delivery fee + free-delivery threshold (client to confirm). */
(function () {
  'use strict';

  var WHATSAPP_NUMBER = '27689235818'; // Jozi Java WhatsApp Business (no +, no leading 0)
  var CART_KEY = 'jj_cart_v1';
  var CUSTOMER_KEY = 'jj_customer_v1';

  var FREE_DELIVERY = 500; // PLACEHOLDER: free courier delivery over R500
  var DELIVERY_FEE = 75;   // PLACEHOLDER: flat SA courier fee under the threshold

  /* Grind list — the e-commerce strategy doc flags "grind defaults to Filter Ground" as its
     critical defect, so nothing is pre-selected: the customer must choose (whole bean is the
     safe default for freshness, but the choice stays explicit). */
  var GRINDS = ['Whole bean', 'Espresso', 'Plunger', 'Filter', 'Moka pot', 'Aeropress'];

  /* ---------- tiny helpers ---------- */
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function money(n) { return 'R' + Number(n || 0).toFixed(2); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- cart state ---------- */
  function load() {
    try { var v = JSON.parse(localStorage.getItem(CART_KEY)); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  var cart = load();

  function save() {
    try { localStorage.setItem(CART_KEY, JSON.stringify(cart)); } catch (e) {}
    syncBadges();
  }

  function itemKey(it) { return it.sku + '|' + it.size + '|' + it.grind; }
  function count() { return cart.reduce(function (n, it) { return n + it.qty; }, 0); }
  function subtotal() { return cart.reduce(function (n, it) { return n + it.qty * it.price; }, 0); }
  function lineTotal(it) { return it.qty * it.price; }

  function deliveryFee(method, sub) {
    if (method === 'collect') return 0;
    return sub >= FREE_DELIVERY ? 0 : DELIVERY_FEE;
  }
  function currentMethod() {
    var r = $('input[name="jj-delivery"]:checked');
    return r ? r.value : 'courier';
  }

  function addItem(data) {
    var qty = Math.max(1, parseInt(data.qty, 10) || 1);
    var key = data.sku + '|' + data.size + '|' + data.grind;
    for (var i = 0; i < cart.length; i++) {
      if (itemKey(cart[i]) === key) { cart[i].qty = Math.min(99, cart[i].qty + qty); save(); return cart[i]; }
    }
    var it = {
      sku: data.sku, name: data.name, size: data.size, grind: data.grind,
      price: Number(data.price) || 0, qty: Math.min(99, qty), img: data.img || ''
    };
    cart.push(it); save(); return it;
  }
  function setQty(key, qty) {
    qty = Math.max(0, Math.min(99, parseInt(qty, 10) || 0));
    for (var i = 0; i < cart.length; i++) {
      if (itemKey(cart[i]) === key) {
        if (qty === 0) cart.splice(i, 1); else cart[i].qty = qty;
        save(); return;
      }
    }
  }
  function removeItem(key) {
    cart = cart.filter(function (it) { return itemKey(it) !== key; });
    save();
  }
  function clearCart() { cart = []; save(); }

  /* ---------- toast ---------- */
  var toastEl, toastTimer;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.id = 'jj-toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 2600);
  }

  /* ---------- nav badge (every page) ---------- */
  function injectNavCart() {
    var nav = $('ul.navbar-nav');
    if (!nav || $('.jj-nav-cart', nav)) return;
    var li = document.createElement('li');
    li.className = 'nav-item jj-nav-cart';
    li.innerHTML = '<a href="cart.html" class="nav-link">Cart <span class="jj-cart-badge" hidden></span></a>';
    nav.appendChild(li);
  }
  function syncBadges() {
    var n = count();
    $$('.jj-cart-badge').forEach(function (b) {
      b.textContent = n;
      if (n > 0) b.removeAttribute('hidden'); else b.setAttribute('hidden', '');
    });
  }

  /* ---------- catalog cards: grind selects + add to cart ---------- */
  function fillGrindSelects() {
    $$('select.jj-grind').forEach(function (sel) {
      if (sel.dataset.filled) return;
      sel.dataset.filled = '1';
      var keep = sel.value;
      sel.innerHTML = '<option value="">Choose grind&hellip;</option>' +
        GRINDS.map(function (g) { return '<option value="' + esc(g) + '">' + esc(g) + '</option>'; }).join('');
      sel.value = keep;
    });
  }

  function activeSize(card) {
    var active = $('.jj-size.active', card);
    var group = $('.jj-sizes', card);
    var btn = active || (group && $('.jj-size', group));
    return btn ? btn.textContent.trim() : '';
  }

  function addFromCard(card) {
    var group = $('.jj-sizes', card);
    var size = activeSize(card);
    var prices = {};
    try { prices = JSON.parse(group.getAttribute('data-prices') || '{}'); } catch (e) {}
    var price = prices[size];
    if (!size || price == null) { toast('Pick a bag size first'); return; }
    var grindSel = $('select.jj-grind', card);
    var grind = grindSel ? grindSel.value : '';
    if (grindSel && !grind) {
      toast('Choose a grind first — whole bean or ground');
      grindSel.focus();
      return;
    }
    if (!grind) grind = 'Whole bean';
    var name = card.dataset.name || (card.querySelector('h3') ? card.querySelector('h3').textContent.trim() : 'Coffee');
    var it = addItem({
      sku: card.dataset.sku || name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
      name: name, size: size, grind: grind, price: price, img: card.dataset.img || '', qty: 1
    });
    toast('Added: ' + it.name + ' · ' + it.size + ' · ' + it.grind);
    renderPage();
  }

  /* Size pills: click swaps the shown card price; re-click clears back to "from" (was shop.js) */
  function pillClick(btn) {
    var group = btn.parentNode;
    var card = btn.closest('.jj-card');
    if (!card) return;
    var priceEl = $('.jj-price span', card);
    var prices = {};
    try { prices = JSON.parse(group.getAttribute('data-prices') || '{}'); } catch (e) {}
    var wasActive = btn.classList.contains('active');
    $$('.jj-size', group).forEach(function (b) { b.classList.remove('active'); });
    if (wasActive) {
      var min = Math.min.apply(null, Object.keys(prices).map(function (k) { return prices[k]; }));
      if (priceEl) priceEl.textContent = 'from ' + money(min);
    } else {
      btn.classList.add('active');
      if (priceEl) priceEl.textContent = money(prices[btn.textContent.trim()]);
    }
  }

  function delegateClicks() {
    document.addEventListener('click', function (e) {
      var t = e.target;
      var size = t.closest && t.closest('.jj-size');
      if (size) { pillClick(size); return; }
      var add = t.closest && t.closest('.jj-add');
      if (add) {
        e.preventDefault();
        var card = add.closest('.jj-card') || add.closest('.menu-entry');
        if (card) addFromCard(card); else toast('Sorry — could not read that product');
        return;
      }
      var q = t.closest && t.closest('.jj-qty button');
      if (q) {
        var row = q.closest('[data-key]');
        if (!row) return;
        var input = $('.jj-qty input', row);
        var step = parseInt(q.dataset.step, 10) || 0;
        setQty(row.dataset.key, (parseInt(input.value, 10) || 0) + step);
        renderPage();
        return;
      }
      var rm = t.closest && t.closest('.jj-line-remove');
      if (rm) {
        var r2 = rm.closest('[data-key]');
        if (!r2) return;
        removeItem(r2.dataset.key);
        toast('Removed from cart');
        renderPage();
      }
    });
  }

  /* ---------- cart page ---------- */
  function renderCartPage() {
    var body = $('#jj-cart-body');
    if (!body) return;
    var empty = $('#jj-cart-empty');
    var wrap = $('#jj-cart-table-wrap');
    var summary = $('#jj-cart-summary');
    var sub = subtotal();

    if (!cart.length) {
      body.innerHTML = '';
      if (wrap) wrap.hidden = true;
      if (summary) summary.hidden = true;
      if (empty) empty.hidden = false;
      return;
    }
    if (wrap) wrap.hidden = false;
    if (summary) summary.hidden = false;
    if (empty) empty.hidden = true;

    body.innerHTML = cart.map(function (it) {
      return '<tr class="text-center" data-key="' + esc(itemKey(it)) + '">' +
        '<td class="product-remove"><button type="button" class="jj-line-remove" aria-label="Remove ' + esc(it.name) + '"><span class="icon-close"></span></button></td>' +
        '<td class="image-prod"><div class="img" style="background-image:url(' + esc(it.img) + ')"></div></td>' +
        '<td class="product-name"><h3>' + esc(it.name) + '</h3><p>' + esc(it.size) + ' &middot; ' + esc(it.grind) + '</p></td>' +
        '<td class="price">' + money(it.price) + '</td>' +
        '<td class="quantity"><div class="jj-qty">' +
          '<button type="button" data-step="-1" aria-label="Decrease quantity">&minus;</button>' +
          '<input class="quantity form-control" value="' + it.qty + '" readonly aria-label="Quantity">' +
          '<button type="button" data-step="1" aria-label="Increase quantity">+</button>' +
        '</div></td>' +
        '<td class="total">' + money(lineTotal(it)) + '</td>' +
        '</tr>';
    }).join('');

    var fee = deliveryFee(currentMethod(), sub);
    var subEl = $('#jj-sum-subtotal'); if (subEl) subEl.textContent = money(sub);
    var feeEl = $('#jj-sum-delivery'); if (feeEl) feeEl.textContent = fee === 0 ? 'Free' : money(fee);
    var totEl = $('#jj-sum-total'); if (totEl) totEl.textContent = money(sub + fee);
    var note = $('#jj-delivery-note');
    if (note) {
      if (sub >= FREE_DELIVERY) note.innerHTML = 'Free nationwide courier delivery unlocked.';
      else note.innerHTML = 'Add ' + money(FREE_DELIVERY - sub) + ' more for free courier delivery (over ' + money(FREE_DELIVERY).replace('.00', '') + '). Prefer to collect? The Roastery, Douglasdale — free.';
    }
  }

  /* ---------- checkout page ---------- */
  function customer() {
    try { return JSON.parse(localStorage.getItem(CUSTOMER_KEY)) || {}; } catch (e) { return {}; }
  }

  function renderCheckoutPage() {
    var lines = $('#jj-order-lines');
    if (!lines) return;
    var empty = $('#jj-checkout-empty');
    var grid = $('#jj-checkout-grid');
    if (!cart.length) {
      if (grid) grid.hidden = true;
      if (empty) empty.hidden = false;
      return;
    }
    if (grid) grid.hidden = false;
    if (empty) empty.hidden = true;

    lines.innerHTML = cart.map(function (it) {
      return '<p class="d-flex jj-order-line"><span>' + esc(it.name) + ' &middot; ' + esc(it.size) + ' &middot; ' + esc(it.grind) +
        ' <em>&times;' + it.qty + '</em></span><span>' + money(lineTotal(it)) + '</span></p>';
    }).join('');

    var sub = subtotal();
    var fee = deliveryFee(currentMethod(), sub);
    $('#jj-sum-subtotal').textContent = money(sub);
    $('#jj-sum-delivery').textContent = fee === 0 ? 'Free' : money(fee);
    $('#jj-sum-total').textContent = money(sub + fee);

    var note = $('#jj-delivery-note');
    if (note) {
      note.textContent = sub >= FREE_DELIVERY
        ? 'Free courier delivery — your order is over ' + money(FREE_DELIVERY).replace('.00', '') + '.'
        : 'Courier ' + money(DELIVERY_FEE) + ' — free over ' + money(FREE_DELIVERY).replace('.00', '') + '. Collect at The Roastery is always free.';
    }
  }

  function orderRef() {
    return 'JJ-' + Date.now().toString(36).toUpperCase().slice(-5);
  }

  function buildOrderMessage(ref) {
    var it = {
      first: ($('#jj-first') || {}).value || '',
      last: ($('#jj-last') || {}).value || '',
      email: ($('#jj-email') || {}).value || '',
      phone: ($('#jj-phone') || {}).value || '',
      street: ($('#jj-street') || {}).value || '',
      suburb: ($('#jj-suburb') || {}).value || '',
      city: ($('#jj-city') || {}).value || '',
      postal: ($('#jj-postal') || {}).value || '',
      notes: ($('#jj-notes') || {}).value || ''
    };
    var method = currentMethod();
    var sub = subtotal();
    var fee = deliveryFee(method, sub);
    var lines = cart.map(function (c, i) {
      return (i + 1) + '. ' + c.name + ' — ' + c.size + ', ' + c.grind + ' × ' + c.qty + ' — ' + money(lineTotal(c));
    }).join('\n');

    var msg = 'Hi Jozi Java! I would like to place an order (' + ref + '):\n\n' + lines + '\n\n' +
      'Subtotal: ' + money(sub) + '\n' +
      'Delivery: ' + (fee === 0 ? (method === 'collect' ? 'Collect — The Roastery, Douglasdale' : 'Free courier') : money(fee)) + '\n' +
      'Total: ' + money(sub + fee) + '\n\n' +
      'Name: ' + it.first + ' ' + it.last + '\n' +
      'Phone: ' + it.phone + '\n' +
      'Email: ' + it.email + '\n';
    if (method === 'collect') {
      msg += 'Fulfilment: Collect from The Roastery (Douglasdale)\n';
    } else {
      msg += 'Deliver to: ' + [it.street, it.suburb, it.city, it.postal].filter(Boolean).join(', ') + '\n';
    }
    if (it.notes) msg += 'Notes: ' + it.notes + '\n';
    msg += '\n(PLEASE PAYMENT LINK: confirm stock and send a secure payment link.)';
    return msg;
  }

  function validateCheckout() {
    var form = $('#jj-checkout-form');
    var method = currentMethod();
    var need = ['jj-first', 'jj-last', 'jj-email', 'jj-phone'];
    if (method === 'courier') need = need.concat(['jj-street', 'jj-city', 'jj-postal']);
    var firstBad = null;
    need.forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      var ok = (el.value || '').trim().length > 0;
      if (el.type === 'email') ok = ok && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim());
      el.classList.toggle('is-invalid', !ok);
      if (!ok && !firstBad) firstBad = el;
    });
    var popia = $('#jj-popia');
    if (popia && !popia.checked) {
      popia.classList.add('is-invalid');
      if (!firstBad) firstBad = popia;
      toast('Please accept the POPIA notice to continue');
    } else if (popia) popia.classList.remove('is-invalid');

    if (firstBad) {
      if (firstBad.id !== 'jj-popia') toast('Please complete the highlighted fields');
      if (firstBad.focus) firstBad.focus();
      return false;
    }
    return true;
  }

  function placeOrder() {
    if (!cart.length) { toast('Your cart is empty'); return; }
    if (!validateCheckout()) return;

    var ref = orderRef();
    var msg = buildOrderMessage(ref);
    var url = 'https://wa.me/' + WHATSAPP_NUMBER + '?text=' + encodeURIComponent(msg);
    var win = window.open(url, '_blank');

    /* remember details for the next order (convenience only, same device) */
    try {
      localStorage.setItem(CUSTOMER_KEY, JSON.stringify({
        first: $('#jj-first').value, last: $('#jj-last').value, email: $('#jj-email').value,
        phone: $('#jj-phone').value, street: $('#jj-street') ? $('#jj-street').value : '',
        suburb: $('#jj-suburb') ? $('#jj-suburb').value : '', city: $('#jj-city') ? $('#jj-city').value : '',
        postal: $('#jj-postal') ? $('#jj-postal').value : ''
      }));
    } catch (e) {}

    var grid = $('#jj-checkout-grid');
    var done = $('#jj-order-confirm');
    if (grid) grid.hidden = true;
    if (done) {
      done.hidden = false;
      var refEl = $('#jj-confirm-ref'); if (refEl) refEl.textContent = ref;
      var link = $('#jj-confirm-link'); if (link) link.href = url;
      if (!win) { var warn = $('#jj-confirm-warn'); if (warn) warn.hidden = false; }
    }
    clearCart();
    window.scrollTo({ top: (done || document.body).offsetTop - 80, behavior: 'smooth' });
  }

  function prefillCustomer() {
    var c = customer();
    Object.keys(c).forEach(function (k) {
      var id = { first: 'jj-first', last: 'jj-last', email: 'jj-email', phone: 'jj-phone', street: 'jj-street', suburb: 'jj-suburb', city: 'jj-city', postal: 'jj-postal' }[k];
      var el = id && document.getElementById(id);
      if (el && !el.value) el.value = c[k];
    });
  }

  function renderPage() { renderCartPage(); renderCheckoutPage(); syncBadges(); }

  /* ---------- init ---------- */
  function init() {
    injectNavCart();
    fillGrindSelects();
    delegateClicks();

    /* cart page */
    var toCheckout = $('#jj-to-checkout');
    var proceed = $('#jj-proceed');
    if (proceed) {
      proceed.addEventListener('click', function (e) {
        if (!cart.length) { e.preventDefault(); toast('Your cart is empty'); }
      });
    }
    if (toCheckout) toCheckout.addEventListener('click', function (e) { e.preventDefault(); placeOrder(); });

    /* checkout page */
    $$('input[name="jj-delivery"]').forEach(function (r) {
      r.addEventListener('change', function () {
        var courier = currentMethod() === 'courier';
        $$('.jj-address-field').forEach(function (f) { f.style.display = courier ? '' : 'none'; });
        renderPage();
      });
    });
    var place = $('#jj-place-order');
    if (place) place.addEventListener('click', function (e) { e.preventDefault(); placeOrder(); });
    var qtyBtns = $$('.jj-qty button');
    if (qtyBtns.length) qtyBtns.forEach(function (b) { b.addEventListener('change', renderPage); });
    prefillCustomer();

    renderPage();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  /* expose a tiny API (handy for tests / future pages) */
  window.JoziCart = {
    add: addItem, setQty: setQty, remove: removeItem, clear: clearCart,
    items: function () { return cart.slice(); },
    count: count, subtotal: subtotal, freeDelivery: FREE_DELIVERY, deliveryFee: DELIVERY_FEE
  };
})();
