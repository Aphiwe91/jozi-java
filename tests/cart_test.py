#!/usr/bin/env python3
"""Jozi Java cart smoke test — shop → cart → checkout → WhatsApp handoff.

Needs the preview server on :8002 and the folder served from coffee1-v1.0.0/:
    python3 -m http.server 8002 --bind ::
    python3 tests/cart_test.py

Headless gotchas handled here:
  - the template loader (#ftco-loader) only fades on window.load
  - .ftco-animate elements sit at opacity 0 until jQuery waypoints fire
  - html{scroll-behavior:smooth} breaks clicks in headless Chromium
"""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

BASE = "http://localhost:8002/"
WHATSAPP = "27689235818"

RESULTS = []


def check(name, cond, extra=""):
    RESULTS.append((name, bool(cond), extra))
    print(("PASS " if cond else "FAIL ") + name + (("  -> " + str(extra)) if extra and not cond else ""))


def make_driver():
    opts = Options()
    opts.binary_location = "/usr/bin/chromium"
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1400,1200")
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)


PREP = """
  document.documentElement.style.scrollBehavior = 'auto';
  var l = document.getElementById('ftco-loader'); if (l) l.remove();
  document.querySelectorAll('.ftco-animate').forEach(function(e){ e.classList.remove('ftco-animate'); e.style.opacity = 1; });
"""


def prep(driver):
    driver.execute_script(PREP)


def toast_text(driver):
    return driver.execute_script("var t=document.getElementById('jj-toast'); return t ? t.textContent : '';")


def badge(driver):
    return driver.execute_script(
        "var b=document.querySelector('.jj-cart-badge');"
        "if(!b) return ['missing', null];"
        "return [b.hidden ? 'hidden' : b.textContent.trim(), b.textContent.trim()];"
    )


def cart_state(driver):
    return driver.execute_script(
        "return {items: window.JoziCart.items(), count: window.JoziCart.count(), subtotal: window.JoziCart.subtotal()};"
    )


def text_of(driver, css):
    return driver.execute_script(
        "var e=document.querySelector(arguments[0]); return e ? e.textContent.trim() : null;", css
    )


def main():
    d = make_driver()
    try:
        # ---------- shop: badge, size pills, grind gate, add ----------
        d.get(BASE + "shop.html")
        prep(d)
        d.execute_script("localStorage.removeItem('jj_cart_v1'); localStorage.removeItem('jj_customer_v1');")
        d.refresh()
        prep(d)
        time.sleep(0.4)

        check("nav cart link injected", d.find_element("css selector", ".jj-nav-cart a").get_attribute("href").endswith("cart.html"))
        check("badge hidden when cart empty", badge(d)[0] == "hidden", badge(d))

        # grind gate: add without grind -> toast, nothing added
        d.find_element("css selector", ".jj-card-wrap .jj-add").click()
        time.sleep(0.25)
        check("grind required (toast shown)", "grind" in toast_text(d).lower(), toast_text(d))
        check("nothing added without grind", cart_state(d)["count"] == 0, cart_state(d))

        # size pill swaps the price
        d.find_element("css selector", ".jj-card-wrap .jj-size:nth-child(2)").click()
        time.sleep(0.2)
        check("500g pill price shown", "R85.00" in text_of(d, ".jj-card-wrap .jj-price span"), text_of(d, ".jj-card-wrap .jj-price span"))

        # grind select filled by cart.js + add
        grind_opts = d.execute_script("return document.querySelector('select.jj-grind').options.length;")
        check("grind select populated", grind_opts >= 6, grind_opts)
        d.execute_script(
            "var s=document.querySelector('.jj-card-wrap select.jj-grind'); s.value='Espresso';"
            "s.dispatchEvent(new Event('change', {bubbles:true}));"
        )
        d.find_element("css selector", ".jj-card-wrap .jj-add").click()
        time.sleep(0.3)
        check("toast confirms add", "added" in toast_text(d).lower(), toast_text(d))
        check("badge shows 1", badge(d)[0] == "1", badge(d))

        # second product: decaf 250g Filter
        d.execute_script(
            "var cards=document.querySelectorAll('.jj-card-wrap'); var c=cards[2];"
            "var s=c.querySelector('select.jj-grind'); s.value='Filter';"
            "c.querySelector('.jj-add').click();"
        )
        time.sleep(0.3)
        st = cart_state(d)
        check("two distinct lines", len(st["items"]) == 2, st)
        check("subtotal 85 + 52 = 137", abs(st["subtotal"] - 137) < 0.001, st["subtotal"])
        check("badge shows 2", badge(d)[0] == "2", badge(d))

        # adding the same line again merges qty instead of duplicating
        d.execute_script(
            "var c=document.querySelectorAll('.jj-card-wrap')[2];"
            "var s=c.querySelector('select.jj-grind'); s.value='Filter'; c.querySelector('.jj-add').click();"
        )
        time.sleep(0.3)
        st = cart_state(d)
        check("same line merges (still 2 lines, qty 2)", len(st["items"]) == 2 and st["count"] == 3, st)

        # ---------- cart page ----------
        d.get(BASE + "cart.html")
        prep(d)
        time.sleep(0.4)
        rows = d.find_elements("css selector", "#jj-cart-body tr")
        check("cart renders 2 rows", len(rows) == 2, len(rows))
        check("cart line shows size + grind", "500g" in rows[0].text and "Espresso" in rows[0].text, rows[0].text)
        # 500g wilds ×1 (R85) + decaf 250g ×2 (R104) = R189 — the twice-added decaf merged
        check("subtotal rendered R189.00", text_of(d, "#jj-sum-subtotal") == "R189.00", text_of(d, "#jj-sum-subtotal"))
        check("delivery R75.00 under R500", text_of(d, "#jj-sum-delivery") == "R75.00", text_of(d, "#jj-sum-delivery"))
        check("total R264.00", text_of(d, "#jj-sum-total") == "R264.00", text_of(d, "#jj-sum-total"))

        # qty stepper: +1 on the wilds line -> R170 + R104 = R274
        d.find_element("css selector", "#jj-cart-body tr:first-child .jj-qty button[data-step='1']").click()
        time.sleep(0.35)
        check("qty stepper updates subtotal (R274.00)", text_of(d, "#jj-sum-subtotal") == "R274.00", text_of(d, "#jj-sum-subtotal"))

        # stepping a line down to zero removes it
        d.find_element("css selector", "#jj-cart-body tr:first-child .jj-qty button[data-step='-1']").click()
        time.sleep(0.35)
        d.find_element("css selector", "#jj-cart-body tr:first-child .jj-qty button[data-step='-1']").click()
        time.sleep(0.35)
        check("stepping to 0 drops the line", len(d.find_elements("css selector", "#jj-cart-body tr")) == 1,
              len(d.find_elements("css selector", "#jj-cart-body tr")))

        # remove the remaining line
        d.find_element("css selector", "#jj-cart-body tr:first-child .jj-line-remove").click()
        time.sleep(0.35)
        check("remove leaves 0 rows", len(d.find_elements("css selector", "#jj-cart-body tr")) == 0)
        check("empty state after removing all", d.execute_script(
            "var e=document.getElementById('jj-cart-empty'); return e && !e.hidden;"))

        # free delivery threshold messaging
        d.execute_script(
            "window.JoziCart.clear(); window.JoziCart.add({sku:'wilds',name:'The Wilds Roast',size:'1kg',grind:'Whole bean',price:129,qty:5});"
        )
        d.refresh()
        prep(d)
        time.sleep(0.35)
        check("free courier over R500", text_of(d, "#jj-sum-delivery") == "Free", text_of(d, "#jj-sum-delivery"))
        check("free-delivery note", "free" in (text_of(d, "#jj-delivery-note") or "").lower(), text_of(d, "#jj-delivery-note"))

        # empty state after clearing
        d.execute_script("window.JoziCart.clear();")
        d.refresh()
        prep(d)
        time.sleep(0.35)
        empty_visible = d.execute_script(
            "var e=document.getElementById('jj-cart-empty'); return e && !e.hidden && e.offsetHeight > 0;"
        )
        check("empty state shows", empty_visible)
        check("table hidden when empty", d.execute_script("return document.getElementById('jj-cart-table-wrap').hidden;"))

        # ---------- checkout ----------
        d.execute_script(
            "window.JoziCart.add({sku:'wilds',name:'The Wilds Roast',size:'500g',grind:'Plunger',price:85,qty:2});"
            "window.JoziCart.add({sku:'decaf',name:'Douglasdale Decaf',size:'250g',grind:'Filter',price:52,qty:1});"
        )
        d.get(BASE + "checkout.html")
        prep(d)
        time.sleep(0.4)
        check("checkout renders 2 order lines", len(d.find_elements("css selector", "#jj-order-lines .jj-order-line")) == 2)
        check("checkout subtotal R222.00", text_of(d, "#jj-sum-subtotal") == "R222.00", text_of(d, "#jj-sum-subtotal"))

        # collect switches delivery to free and hides the address fields
        d.find_element("css selector", "input[name='jj-delivery'][value='collect']").click()
        time.sleep(0.3)
        check("collect = free delivery", text_of(d, "#jj-sum-delivery") == "Free", text_of(d, "#jj-sum-delivery"))
        addr_hidden = d.execute_script(
            "var f=document.querySelector('.jj-address-field'); return f && f.style.display === 'none';"
        )
        check("address fields hidden for collection", addr_hidden)
        d.find_element("css selector", "input[name='jj-delivery'][value='courier']").click()
        time.sleep(0.3)

        # stub window.open so headless can't open a real tab
        d.execute_script("window.open = function(u){ window.__wa = u; return { closed:false }; };")

        # validation: empty form refused
        d.find_element("css selector", "#jj-place-order").click()
        time.sleep(0.3)
        check("blocked without details", d.execute_script("return !window.__wa;"))
        check("invalid field flagged", len(d.find_elements("css selector", ".is-invalid")) > 0)

        # fill in and submit
        fields = {
            "jj-first": "Thabo", "jj-last": "Mokoena", "jj-email": "thabo@example.co.za",
            "jj-phone": "0821234567", "jj-street": "12 Beyers Naude", "jj-suburb": "Northcliff",
            "jj-city": "Johannesburg", "jj-postal": "2195", "jj-notes": "Leave at reception",
        }
        for fid, val in fields.items():
            d.find_element("css selector", "#" + fid).send_keys(val)
        d.find_element("css selector", "#jj-popia").click()
        d.find_element("css selector", "#jj-place-order").click()
        time.sleep(0.5)

        wa = d.execute_script("return window.__wa || '';")
        check("whatsapp handoff url built", wa.startswith("https://wa.me/" + WHATSAPP + "?text="), wa[:80])
        body = d.execute_script("return decodeURIComponent(window.__wa.split('?text=')[1] || '');")
        check("message has product line", "The Wilds Roast: 500g, Plunger × 2: R170.00" in body, body[:400])
        check("message has totals", "Total: R297.00" in body, body[:400])
        check("message has customer", "Thabo Mokoena" in body and "0821234567" in body, body[:400])
        check("message has address", "12 Beyers Naude" in body and "2195" in body, body[:400])
        check("confirmation panel visible", d.execute_script(
            "var c=document.getElementById('jj-order-confirm'); return c && !c.hidden && c.offsetHeight > 0;"))
        check("reference shown", (text_of(d, "#jj-confirm-ref") or "").startswith("JJ"), text_of(d, "#jj-confirm-ref"))
        check("order reference has no dash", "-" not in text_of(d, "#jj-confirm-ref"))
        # Opening a window is not proof of sending: keep the bag so orders are not lost.
        check("cart preserved after preparing WhatsApp message", badge(d)[0] == "3", badge(d))
        check("personal details not saved without opt-in", d.execute_script("return localStorage.getItem('jj_customer_v1') === null;"))
        check("confirmation is honest about submission", "not yet submitted" in (text_of(d, "#jj-order-confirm") or "").lower())

        # A blocked popup still gets a retry link and retains the bag.
        d.get(BASE + "checkout.html")
        prep(d)
        d.execute_script("window.open = function(u){ window.__wa = u; return null; };")
        for fid in ["jj-first", "jj-last", "jj-email", "jj-phone"]:
            d.find_element("css selector", "#" + fid).send_keys(fields[fid])
        d.find_element("css selector", "input[name='jj-delivery'][value='collect']").click()
        d.find_element("css selector", "#jj-popia").click()
        d.find_element("css selector", "#jj-remember").click()
        d.find_element("css selector", "#jj-place-order").click()
        check("popup blocker warning visible", d.find_element("css selector", "#jj-confirm-warn").is_displayed())
        check("popup retry link has prepared message", "?text=" in d.find_element("css selector", "#jj-confirm-link").get_attribute("href"))
        check("blocked popup retains bag", cart_state(d)["count"] == 3)
        check("remember details requires explicit opt-in", d.execute_script("return JSON.parse(localStorage.getItem('jj_customer_v1')).remember === true;"))
        d.get(BASE + "checkout.html")
        prep(d)
        check("opted-in details prefilled", d.find_element("css selector", "#jj-first").get_attribute("value") == "Thabo")
        d.find_element("css selector", "#jj-forget-details").click()
        check("forget details removes personal storage", d.execute_script("return localStorage.getItem('jj_customer_v1') === null;"))

        # Clear only after the customer explicitly chooses to empty the bag.
        d.find_element("css selector", "input[name='jj-delivery'][value='collect']").click()
        d.find_element("css selector", "#jj-popia").click()
        d.execute_script("window.open = function(){return null;};")
        d.find_element("css selector", "#jj-place-order").click()
        d.execute_script("document.getElementById('jj-clear-after-order').click();")
        check("explicit empty-bag action clears cart", cart_state(d)["count"] == 0)

        # ---------- nav badge on a page without cart widgets ----------
        d.get(BASE + "about.html")
        prep(d)
        time.sleep(0.3)
        check("badge renders on other pages", badge(d)[0] == "hidden")
        check("nav cart link on about.html", len(d.find_elements("css selector", ".jj-nav-cart")) == 1)

        # Browser storage is untrusted: discard malformed items and reprice valid items.
        d.execute_script("localStorage.setItem('jj_cart_v1', JSON.stringify([null, {}, {sku:'fake',qty:9}, {sku:'wilds',name:'Injected',size:'1kg',grind:'Whole bean',price:0.01,qty:999,img:'javascript:bad'}]));")
        d.refresh()
        state = cart_state(d)
        check("malformed stored items discarded", len(state["items"]) == 1, state)
        check("stored price and quantity normalized", state["items"][0]["price"] == 129 and state["count"] == 99, state)
        check("stored product name trusted from catalogue", state["items"][0]["name"] == "The Wilds Roast")
        d.execute_script("localStorage.setItem('jj_cart_v1', '{broken');")
        d.refresh()
        check("corrupt storage does not break cart", cart_state(d)["count"] == 0)

    finally:
        d.quit()

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("\n%d/%d assertions passed" % (passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
