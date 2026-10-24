#!/usr/bin/env python3
"""Selenium site QA: responsive pages, filters, enquiry handoffs and accessibility.

Requires :8002, Selenium, /usr/bin/chromium and /usr/bin/chromedriver.
No animation/preloader hacks: all real page content must remain available naturally.
"""
import json
import sys
from pathlib import Path
from urllib.parse import unquote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://localhost:8002/'
RESULTS = []


def check(name, condition, extra=None):
    RESULTS.append((name, bool(condition)))
    print(('PASS ' if condition else 'FAIL ') + name + (f' → {extra}' if not condition and extra else ''))


def make_driver():
    options = Options()
    options.binary_location = '/usr/bin/chromium'
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1440,1100')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    return webdriver.Chrome(service=Service('/usr/bin/chromedriver'), options=options)


def text(driver, selector):
    return driver.execute_script('return document.querySelector(arguments[0]).textContent.trim();', selector)


def fill(driver, values):
    for id_, value in values.items():
        element = driver.find_element('id', id_)
        element.clear()
        element.send_keys(value)


def submit(driver, selector):
    driver.execute_script('document.querySelector(arguments[0]).requestSubmit();', selector)


def stub_popup(driver, blocked=False):
    driver.execute_script('window.__messageUrl = null; window.open = function(url){window.__messageUrl = url; return ' + ('null' if blocked else '{}') + ';};')


def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 8)
    try:
        driver.execute_cdp_cmd('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-reduced-motion', 'value': 'reduce'}]})
        pages = sorted(p.name for p in ROOT.glob('*.html'))
        for width in [1440, 768, 390, 320]:
            driver.set_window_size(width, 1050)
            for page in pages:
                driver.get(BASE + page)
                wait.until(lambda d: d.execute_script('return !!window.JoziCart;'))
                dims = driver.execute_script('return [document.documentElement.scrollWidth, document.documentElement.clientWidth];')
                check(f'{page} at {width}px: no horizontal overflow', dims[0] <= dims[1] + 1, dims)
                check(f'{page} at {width}px: heading visible', driver.find_element('tag name', 'h1').is_displayed())
                broken = driver.execute_script('return Array.from(document.images).filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src);')
                check(f'{page} at {width}px: images load', not broken, broken)
                errors = [e['message'] for e in driver.get_log('browser') if e['level'] == 'SEVERE']
                check(f'{page} at {width}px: no browser errors', not errors, errors)
                fonts = driver.execute_script("""
                    var expected = getComputedStyle(document.documentElement).fontFamily;
                    var mismatches = [...document.querySelectorAll('body *')].filter(function (element) {
                      if (['SCRIPT','STYLE','NOSCRIPT'].includes(element.tagName)) return false;
                      var text = [...element.childNodes].some(function (node) { return node.nodeType === 3 && node.textContent.trim(); });
                      return (text || ['INPUT','SELECT','TEXTAREA','BUTTON','OPTION'].includes(element.tagName)) && getComputedStyle(element).fontFamily !== expected;
                    }).map(function (element) { return element.tagName + '.' + element.className; });
                    return {stack:expected,mismatches:mismatches};
                """)
                check(f'{page} at {width}px: SF stack applied throughout', 'SF Pro Text' in fonts['stack'] and not fonts['mismatches'], fonts)
                dashes = driver.execute_script("""
                    return [...document.querySelectorAll('body *')].filter(function (element) {
                      if (['SCRIPT','STYLE','NOSCRIPT'].includes(element.tagName)) return false;
                      return [...element.childNodes].some(function (node) { return node.nodeType === 3 && /[-\\u2010-\\u2015]/.test(node.textContent); });
                    }).map(function (element) { return element.tagName + ': ' + element.textContent.slice(0, 100); });
                """)
                check(f'{page} at {width}px: no dash punctuation in website copy', not dashes, dashes)

        # Keep the approved pre-redesign appearance as a regression requirement.
        driver.set_window_size(1440, 1100)
        driver.get(BASE + 'index.html')
        heading = text(driver, '.jj-wordmark')
        check('original Equipment & Beans / Delivered headline restored', 'Equipment & Beans' in heading and 'Delivered' in heading)
        check('original desktop hero height restored', driver.execute_script("return document.querySelector('.jj-hero-slides').getBoundingClientRect().height;") == 750)
        check('original 140px desktop logo restored', driver.execute_script("return document.querySelector('.jj-nav-logo').getBoundingClientRect().width;") == 140)
        check('original poster backdrop restored', driver.execute_script("return getComputedStyle(document.body).backgroundImage.includes('jozi-bg-960.webp');"))
        check('square original-style buttons retained', driver.execute_script("return getComputedStyle(document.querySelector('.btn-primary')).borderRadius;") == '0px')
        check('original wholesale photo mosaic restored', len(driver.find_elements('css selector', '.jj-photo-mosaic img')) == 4)
        check('original full-width gallery restored', len(driver.find_elements('css selector', '.jj-home-gallery img')) == 4)
        check('added promotional footer removed', not driver.find_elements('css selector', '.jj-footer-top'))
        stub_popup(driver, blocked=True)
        fill(driver, {'home-name': 'Home Enquiry', 'home-phone': '0821234567', 'home-email': 'home@example.co.za', 'home-message': 'Please help with coffee supply.'})
        submit(driver, '#jj-home-contact-form')
        check('restored homepage form requires consent', driver.execute_script('return window.__messageUrl === null;'))
        driver.execute_script("document.querySelector('#jj-home-contact-form [name=consent]').checked=true;")
        submit(driver, '#jj-home-contact-form')
        check('restored homepage form still prepares message', 'Home Enquiry' in unquote(driver.execute_script('return window.__messageUrl || "";')))
        check('restored homepage form retains retry link', driver.find_element('css selector', '#jj-home-contact-form .jj-form-result a').get_attribute('href').startswith('https://wa.me/27689235818?text='))
        check('dynamic WhatsApp preview uses the SF stack', driver.execute_script("return getComputedStyle(document.querySelector('#jj-home-contact-form pre')).fontFamily === getComputedStyle(document.documentElement).fontFamily;"))

        driver.set_window_size(390, 950)
        driver.get(BASE + 'index.html')
        menu = driver.find_element('css selector', '.jj-menu-toggle')
        check('mobile menu starts collapsed', menu.get_attribute('aria-expanded') == 'false')
        menu.click()
        check('mobile menu opens accessibly', menu.get_attribute('aria-expanded') == 'true' and driver.find_element('id', 'ftco-nav').is_displayed())
        from selenium.webdriver.common.keys import Keys
        menu.send_keys(Keys.ESCAPE)
        check('Escape closes mobile menu', menu.get_attribute('aria-expanded') == 'false')
        check('home reduced motion pauses carousel', driver.find_element('css selector', '.jj-motion-toggle').get_attribute('aria-pressed') == 'true')
        check('home has 5 manual slide controls', len(driver.find_elements('css selector', '.jj-hero-dots button')) == 5)
        driver.execute_script("document.querySelector('.jj-slide-next').click();")
        check('home next control changes slide', '02' in text(driver, '.jj-slide-count'))
        check('inactive slides are inert', driver.execute_script("return [...document.querySelectorAll('.jj-hero-slide:not(.is-active)')].every(s=>s.inert&&s.getAttribute('aria-hidden')==='true');"))
        check('full story available with reduced motion', len(text(driver, '#story-typing')) > 500)

        driver.set_window_size(1440, 1100)
        driver.get(BASE + 'shop.html?q=decaf')
        check('URL search filters coffee', driver.execute_script("return document.querySelectorAll('#jj-grid .jj-card-wrap:not([hidden])').length;") == 1)
        check('search result identifies decaf', '1 roast' in text(driver, '.jj-collection-count'))
        search = driver.find_element('id', 'jj-shop-search')
        search.clear(); search.send_keys('nothing matches this')
        check('shop empty search state visible', driver.find_element('id', 'jj-search-empty').is_displayed())
        driver.execute_script("document.getElementById('jj-clear-search').click();")
        Select(driver.find_element('id', 'jj-sort')).select_by_value('price-desc')
        check('coffee sort works', driver.execute_script("return document.querySelector('#jj-grid > :first-child').dataset.name;") == 'Douglasdale Decaf')
        driver.get(BASE + 'pritchard-street-roast.html')
        check('dedicated product has correct heading', text(driver, 'h1') == 'Pritchard Street Roast')
        driver.execute_script("localStorage.removeItem('jj_cart_v1'); window.JoziCart.clear(); document.querySelector('.jj-product-info .jj-size:nth-child(3)').click(); document.querySelector('.jj-product-info .jj-grind').value='Moka pot'; document.querySelector('.jj-product-info .jj-add').click();")
        item = driver.execute_script('return window.JoziCart.items()[0];')
        check('product page adds correct variant', item['sku'] == 'pritchard' and item['size'] == '1kg' and item['price'] == 139 and item['grind'] == 'Moka pot', item)

        driver.get(BASE + 'equipment.html')
        check('equipment uses the original simple title banner', text(driver, 'h1') == 'Equipment')
        check('equipment catalogue uses factual table rows', driver.find_element('css selector', '.jj-equipment-card').tag_name == 'tr')
        Select(driver.find_element('id', 'equipKind')).select_by_value('automatic')
        Select(driver.find_element('id', 'equipBrand')).select_by_visible_text('Jura')
        Select(driver.find_element('id', 'equipBudget')).select_by_value('80000')
        check('equipment filters combine correctly', '3 equipment options' == text(driver, '#equip-count'))
        Select(driver.find_element('id', 'equipBudget')).select_by_value('30000')
        check('equipment empty state visible', driver.find_element('id', 'equip-empty').is_displayed())
        driver.execute_script("document.querySelector('[data-equipment-reset]').click();")
        wait.until(lambda d: text(d, '#equip-count') == '17 equipment options')
        check('equipment reset restores every model', text(driver, '#equip-count') == '17 equipment options')
        link = driver.find_element('css selector', '#casadio-2 a[href^="finance"]')
        check('equipment finance link carries guide price', 'value=73600' in link.get_attribute('href'))

        driver.get(BASE + 'contact.html?topic=Equipment&message=Please%20quote%20the%20Casadio#enquiry')
        stub_popup(driver, blocked=True)
        check('quote context prefills contact form', driver.find_element('id', 'contact-topic').get_attribute('value') == 'Equipment' and 'Casadio' in driver.find_element('id', 'contact-message').get_attribute('value'))
        fill(driver, {'contact-name': 'Test Customer', 'contact-phone': '0821234567', 'contact-email': 'test@example.co.za'})
        submit(driver, '#jj-contact-form')
        check('contact consent required', driver.execute_script('return window.__messageUrl === null;'))
        driver.execute_script("document.querySelector('#jj-contact-form [name=consent]').checked=true;")
        submit(driver, '#jj-contact-form')
        url = driver.execute_script('return window.__messageUrl || "";')
        check('contact prepares complete WhatsApp message', 'Test Customer' in unquote(url) and 'Casadio' in unquote(url))
        check('contact fallback works with blocked popup', driver.find_element('css selector', '#jj-contact-form .jj-form-result a').get_attribute('href') == url)
        check('contact never claims message received', 'not submitted' in text(driver, '#jj-contact-form .jj-form-result'))
        check('map does not load without consent', len(driver.find_elements('tag name', 'iframe')) == 0)
        check('contact PII not stored automatically', driver.execute_script("return localStorage.getItem('jj_customer_v1') === null;"))

        driver.get(BASE + 'wholesale.html')
        stub_popup(driver)
        fill(driver, {'trade-name': 'Test Buyer', 'trade-business': 'Test Café', 'trade-email': 'trade@example.co.za', 'trade-phone': '0821234567', 'trade-location': 'Sandton'})
        Select(driver.find_element('id', 'trade-type')).select_by_index(1)
        Select(driver.find_element('id', 'trade-volume')).select_by_index(2)
        driver.execute_script("document.querySelector('#jj-trade-form [name=consent]').checked=true;")
        submit(driver, '#jj-trade-form')
        check('trade message includes volumes and business', driver.execute_script("return decodeURIComponent(window.__messageUrl).includes('Test Café') && decodeURIComponent(window.__messageUrl).includes('10 to 25kg');"))

        driver.get(BASE + 'finance.html?asset=Casadio%20Nettuno%202GR&value=73600#calculator')
        stub_popup(driver)
        check('finance asset prefilled from equipment', driver.find_element('id', 'jj-finance-asset').get_attribute('value') == 'Casadio Nettuno 2GR')
        check('finance deposit arithmetic is correct', '7' in text(driver, '#jj-dep') and abs(driver.execute_script("return Number(document.getElementById('jj-value').value) * .1;") - 7360) < .01)
        Select(driver.find_element('id', 'jj-deposit')).select_by_value('0.20')
        check('finance planner updates deposit', '14' in text(driver, '#jj-dep') and '720' in text(driver, '#jj-dep'))
        value = driver.find_element('id', 'jj-value'); value.clear(); value.send_keys('-10')
        check('invalid asset does not generate nonsensical total', text(driver, '#jj-dep') == 'Not available' and driver.find_element('id', 'jj-planner-error').is_displayed())
        value.clear(); value.send_keys('73600')
        for id_ in ['jj-trading', 'jj-turnover', 'jj-vat']:
            Select(driver.find_element('id', id_)).select_by_visible_text('Yes')
        check('finance eligibility indicates criteria, not approval', 'not approval' in text(driver, '#jj-eligibility'))
        Select(driver.find_element('id', 'jj-vat')).select_by_visible_text('No')
        check('finance ineligible answers show alternatives', 'do not meet' in text(driver, '#jj-eligibility'))
        fill(driver, {'jj-biz': 'Test Business', 'jj-person': 'Test Contact', 'finance-email': 'finance@example.co.za', 'finance-phone': '0821234567', 'jj-site': 'Johannesburg'})
        driver.execute_script("document.querySelector('#jj-lead-form [name=consent]').checked=true;")
        submit(driver, '#jj-lead-form')
        message = unquote(driver.execute_script('return window.__messageUrl || "";'))
        check('finance enquiry includes eligibility and asset', 'VAT registered: No' in message and 'Casadio Nettuno 2GR' in message and 'not a credit application' in message)
        check('finance links to real CCS calculator', bool(driver.find_elements('css selector', 'a[href="https://ccs.equipment/#calculator"]')))

        driver.get(BASE + 'tuktuk.html')
        stub_popup(driver)
        Select(driver.find_element('id', 'build-machine')).select_by_value('wega')
        check('build guide recalculates known equipment only', '99' in text(driver, '#build-equipment-total') and '388.19' in text(driver, '#build-equipment-total'))
        submit(driver, '#jj-build-form')
        message = unquote(driver.execute_script('return window.__messageUrl || "";'))
        check('build enquiry carries selected equipment', 'Wega Rover' in message and 'Equipment only guide' in message)
        Select(driver.find_element('id', 'build-machine')).select_by_value('custom')
        check('custom build does not invent a total', 'specify' in text(driver, '#build-equipment-total'))

        driver.get(BASE + 'blog.html')
        driver.find_element('css selector', '[data-journal-filter="equipment"]').click()
        check('journal filter shows one relevant guide', text(driver, '#journal-count') == '1 practical guide')
        driver.find_element('css selector', '[data-journal-filter="all"]').click()
        check('journal resets all guides', text(driver, '#journal-count') == '3 practical guides')

        # Capture reviewable screenshots outside the repository.
        captures = Path('/tmp/opencode/jozi-java')
        captures.mkdir(parents=True, exist_ok=True)
        for page, width in [('index.html', 1440), ('shop.html', 390), ('equipment.html', 1440), ('contact.html', 390)]:
            driver.set_window_size(width, 1000)
            driver.get(BASE + page)
            driver.save_screenshot(str(captures / (page[:-5] + f'-{width}.png')))

        # Content and static navigation stay available when JavaScript is disabled.
        driver.execute_cdp_cmd('Emulation.setScriptExecutionDisabled', {'value': True})
        driver.get(BASE + 'about.html')
        check('no-JS story remains visible', driver.find_element('tag name', 'h1').is_displayed())
        check('no-JS navigation remains available', driver.find_element('id', 'ftco-nav').is_displayed())
        driver.get(BASE + 'index.html')
        check('no-JS first hero stays visible', driver.find_element('css selector', '.jj-hero-slide.is-active h1').is_displayed())
        check('no-JS complete story remains visible', len(text(driver, '#story-typing')) > 500)
    finally:
        driver.quit()
    passed = sum(ok for _, ok in RESULTS)
    print(f'\n{passed}/{len(RESULTS)} site assertions passed')
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
