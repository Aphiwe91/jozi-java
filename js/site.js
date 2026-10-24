/* Shared Jozi Java interactions. No third-party JavaScript or background form service. */
(function () {
  'use strict';

  var $ = function (selector, root) { return (root || document).querySelector(selector); };
  var $$ = function (selector, root) { return Array.prototype.slice.call((root || document).querySelectorAll(selector)); };
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  // Match the catalogue's R12,345.67 guide-price convention on every device.
  var money = function (n) { return 'R' + Number(n).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };

  function setupNavigation() {
    var header = $('#ftco-navbar');
    var toggle = $('.jj-menu-toggle');
    if (!header || !toggle) return;
    document.body.classList.add('jj-menu-ready');
    function close() { header.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); }
    toggle.addEventListener('click', function () {
      var open = header.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    header.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && header.classList.contains('is-open')) { close(); toggle.focus(); }
    });
    $$('a', $('#ftco-nav')).forEach(function (link) { link.addEventListener('click', close); });
    window.matchMedia('(min-width: 992px)').addEventListener('change', close);
    document.addEventListener('click', function (event) { if (!header.contains(event.target)) close(); });
    var top = $('.jj-back-top');
    if (top) {
      var queued = false;
      function update() { top.hidden = window.scrollY < 650; queued = false; }
      window.addEventListener('scroll', function () { if (!queued) { queued = true; requestAnimationFrame(update); } }, { passive: true });
      top.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: reducedMotion.matches ? 'auto' : 'smooth' }); });
      update();
    }
    $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
  }

  /* A prepared message is never labelled as received/sent. Always retain a visible
     retry link, including when popup blockers or WhatsApp itself prevent a handoff. */
  function prepareMessage(message, result) {
    var url = 'https://wa.me/27689235818?text=' + encodeURIComponent(message);
    var win = null;
    try { win = window.open(url, '_blank'); if (win) win.opener = null; } catch (error) { /* retry link below */ }
    result.replaceChildren();
    var text = document.createElement('p');
    text.textContent = 'Your message is prepared, not submitted. Review it and press Send in WhatsApp. If no window opened, use the link below.';
    var link = document.createElement('a');
    link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Open prepared WhatsApp message ↗'; link.className = 'jj-text-link';
    var details = document.createElement('details');
    var summary = document.createElement('summary'); summary.textContent = 'Review the prepared message';
    var preview = document.createElement('pre'); preview.textContent = message;
    details.append(summary, preview); result.append(text, link, details); result.hidden = false;
  }

  function setupForms() {
    $$('[data-whatsapp-form]').forEach(function (form) {
      $$('input, textarea', form).forEach(function (input) {
        input.addEventListener('input', function () { input.setCustomValidity(''); });
      });
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        $$('input[required],textarea[required]', form).forEach(function (input) {
          if (input.type !== 'checkbox') input.setCustomValidity(input.value.trim() ? '' : 'Please complete this field.');
        });
        if (!form.reportValidity()) return;
        var lines = ['Hi Jozi Java! ' + form.dataset.title + ':', ''];
        $$('input[name],select[name],textarea[name]', form).forEach(function (input) {
          if (input.name === 'consent' || input.type === 'checkbox' || input.type === 'hidden') return;
          var value = input.value.trim();
          if (value) lines.push(input.name + ': ' + value);
        });
        if (form.id === 'jj-lead-form') {
          var budget = financeBudget();
          if (!budget) { $('#jj-value').reportValidity(); $('#jj-value').focus(); return; }
          lines.push('', 'Asset: ' + $('#jj-finance-asset').value.trim(), 'Asset guide value (incl. VAT): ' + money(budget.value),
            'Planned deposit: ' + money(budget.deposit), 'Preferred term: ' + $('#jj-term').value + ' months',
            'Preliminary eligibility: ' + eligibilityText(), 'This is an enquiry, not a credit application.');
        }
        lines.push('', 'I agree to share these details with Jozi Java to respond to this enquiry.');
        prepareMessage(lines.join('\n'), $('.jj-form-result', form));
      });
    });
    var params = new URLSearchParams(window.location.search);
    var topic = $('#contact-topic');
    if (topic) {
      var requested = (params.get('topic') || '').slice(0, 100);
      if (requested === 'Tuk Tuk') requested = 'Tuk Tuk conversion';
      if (Array.prototype.some.call(topic.options, function (o) { return o.value === requested; })) topic.value = requested;
      var message = params.get('message');
      if (message) $('#contact-message').value = message.slice(0, 1800);
    }
  }

  function setupEquipment() {
    var form = $('#equipment-filters');
    if (!form) return;
    var search = $('#equipSearch'), kind = $('#equipKind'), brand = $('#equipBrand'), budget = $('#equipBudget');
    var cards = $$('.jj-equipment-card');
    function update() {
      var words = search.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
      var shown = 0;
      cards.forEach(function (card) {
        var text = card.textContent.toLocaleLowerCase();
        var hit = words.every(function (word) { return text.indexOf(word) !== -1; }) &&
          (!kind.value || card.dataset.kind === kind.value) && (!brand.value || card.dataset.brand === brand.value) &&
          (!budget.value || Number(card.dataset.price) <= Number(budget.value));
        card.hidden = !hit; if (hit) shown++;
      });
      $('#equip-count').textContent = shown + (shown === 1 ? ' equipment option' : ' equipment options');
      $('#equip-empty').hidden = shown !== 0;
    }
    form.addEventListener('submit', function (event) { event.preventDefault(); update(); });
    form.addEventListener('input', update); form.addEventListener('change', update);
    form.addEventListener('reset', function () { requestAnimationFrame(update); });
    $('[data-equipment-reset]').addEventListener('click', function () { form.reset(); });
    $$('[data-equipment-shortcut]').forEach(function (a) { a.addEventListener('click', function () { kind.value = a.dataset.equipmentShortcut; update(); }); });
    update();
  }

  function financeBudget() {
    var value = $('#jj-value');
    if (!value || !value.checkValidity()) return null;
    var n = Number(value.value), rate = Number($('#jj-deposit').value);
    if (!Number.isFinite(n) || n < 1000 || n > 10000000) return null;
    return { value: n, deposit: n * rate, remaining: n * (1 - rate) };
  }

  function eligibilityText() {
    var answers = ['jj-trading', 'jj-turnover', 'jj-vat'].map(function (id) { return $('#' + id).value; });
    if (answers.some(function (v) { return !v; })) return 'Answer all three questions for a preliminary eligibility indication.';
    if (answers.every(function (v) { return v === 'Yes'; })) return 'Your answers meet the three published starting criteria. This is not approval; CCS must assess the application.';
    return 'Your answers do not meet all three published CCS starting criteria. You can still enquire about outright purchase or other equipment options.';
  }

  function setupFinance() {
    var form = $('#jj-finance-planner');
    if (!form) return;
    var params = new URLSearchParams(window.location.search);
    var requested = params.get('value');
    if (requested && Number.isFinite(Number(requested)) && Number(requested) >= 1000 && Number(requested) <= 10000000) $('#jj-value').value = requested;
    if (params.get('asset')) $('#jj-finance-asset').value = params.get('asset').slice(0, 150);
    function update() {
      var budget = financeBudget();
      $('#jj-planner-error').hidden = !!budget;
      $('#jj-dep').textContent = budget ? money(budget.deposit) : 'Not available';
      $('#jj-financed').textContent = budget ? money(budget.remaining) : 'Not available';
      $('#jj-deposit-percent').textContent = Math.round(Number($('#jj-deposit').value) * 100) + '%';
    }
    form.addEventListener('input', update); form.addEventListener('change', update);
    form.addEventListener('submit', function (event) { event.preventDefault(); update(); });
    ['jj-trading', 'jj-turnover', 'jj-vat'].forEach(function (id) { $('#' + id).addEventListener('change', function () { $('#jj-eligibility').textContent = eligibilityText(); }); });
    update();
  }

  function setupBuild() {
    var form = $('#jj-build-form');
    if (!form) return;
    function equipmentTotal() {
      var choice = $('#build-machine').value;
      var catalog = window.JoziCatalog.equipment;
      var ids = choice === 'wega' ? ['wega', 'buddy'] : ['casadio-2', 'buddy'];
      return choice === 'custom' ? null : catalog.reduce(function (sum, e) { return sum + (ids.indexOf(e.id) !== -1 ? e.price : 0); }, 0);
    }
    function update() { var total = equipmentTotal(); $('#build-equipment-total').textContent = total === null ? 'Let’s specify it' : money(total); }
    form.addEventListener('change', update);
    form.addEventListener('submit', function (event) {
      event.preventDefault(); var total = equipmentTotal();
      var text = ['Hi Jozi Java! I would like to discuss a Tuk Tuk coffee conversion.', '',
        'Platform: ' + $('#build-base').value, 'Equipment: ' + $('#build-machine').selectedOptions[0].text,
        'Trading site: ' + $('#build-site').value, 'Power: ' + $('#build-power').value,
        total === null ? 'Please recommend an equipment setup.' : 'Equipment only guide (incl. VAT): ' + money(total),
        '', 'Please confirm the vehicle, conversion, power/water, training, delivery and final package price. This is an enquiry, not an order or a finance application.'].join('\n');
      prepareMessage(text, $('#build-result'));
    });
    update();
  }

  function setupJournal() {
    var buttons = $$('[data-journal-filter]');
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        var category = button.dataset.journalFilter, shown = 0;
        buttons.forEach(function (other) { var active = other === button; other.classList.toggle('is-active', active); other.setAttribute('aria-pressed', String(active)); });
        $$('[data-journal-category]').forEach(function (card) { card.hidden = category !== 'all' && card.dataset.journalCategory !== category; if (!card.hidden) shown++; });
        $('#journal-count').textContent = shown + (shown === 1 ? ' practical guide' : ' practical guides');
      });
    });
  }

  function setupMap() {
    var button = $('[data-load-map]'); if (!button) return;
    button.addEventListener('click', function () {
      var frame = document.createElement('iframe');
      frame.src = 'https://www.google.com/maps?q=Jozi+Java+2+Honeyguide+Douglasdale+South+Africa&output=embed';
      frame.title = 'Google Map: Jozi Java, The Roastery, Douglasdale'; frame.referrerPolicy = 'no-referrer'; frame.allowFullscreen = true;
      button.closest('.jj-map-consent').replaceChildren(frame);
    });
  }

  setupNavigation(); setupForms(); setupEquipment(); setupFinance(); setupBuild(); setupJournal(); setupMap();
})();
