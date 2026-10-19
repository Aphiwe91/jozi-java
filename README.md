# Jozi Java — Coffee Roastery Website (Johannesburg)

Multi-page marketing + shop site for Jozi Java, built on the Colorlib "Coffee" template
and rebranded with custom `jj-*` styles.

## Stack

Plain static site — no build step. Open `index.html` or serve the folder:

```bash
python3 -m http.server 8002
# → http://localhost:8002/
```

- `css/style.css` — template CSS + custom brand styles at the end
  (`jj-*` classes, `--jj-ink/milk/leaf/sage/moss` palette, Barlow / Barlow Condensed fonts)
- Navbar: logo sits at the **right end** with the social handles beside it
  (`.jj-nav-right` / `.jj-nav-social`); menu links stay left. `.jj-nav-logo` needs an
  explicit width — the source mark is square and a flex row would otherwise squeeze it.
- Page banner / backdrop: the client poster (`images/jozi/jozi-bg.jpeg`) replaces the
  photo strips behind every page title. It is portrait, so it is drawn whole (`contain`)
  on its own navy field with the slide text on a translucent plaque — a `cover` crop cuts
  the poster in half.
- `js/shop.js` — collection sorting (shop page only)
- `js/cart.js` — localStorage cart: size/grind pickers, nav count badge, cart + checkout
  rendering, WhatsApp order handoff (`wa.me/27689235818`). No payment gateway yet.
- `js/enhancements.js` — sticky nav, scroll reveals, animated counters, WhatsApp/back-to-top FABs
- `images/jozi/jozi-01..47.jpeg` — client photos

## Cart & ordering

Add to Cart is real (localStorage, key `jj_cart_v1`): pick a bag size, choose a grind
(required — the e-commerce strategy flags a silent default grind as its critical defect),
then add. `cart.html` renders the lines with qty steppers and totals; `checkout.html`
collects the customer details and opens WhatsApp with the full order pre-filled. Nothing
is charged online — Jozi Java confirms stock and sends a payment link.

- Delivery rules are `PLACEHOLDER` values in `js/cart.js`: `DELIVERY_FEE` R75, `FREE_DELIVERY` R500,
  collection at The Roastery (Douglasdale) free.
- Test: `python3 tests/cart_test.py` (41 Selenium assertions; needs the :8002 server running)

## Pages

| Page | File |
|---|---|
| Home | `index.html` |
| Shop / collection | `shop.html` |
| Product single | `product-single.html` |
| Cart / checkout | `cart.html`, `checkout.html` |
| Menu | `menu.html` |
| About | `about.html` |
| Equipment, Tuk Tuk, Finance | `equipment.html`, `tuktuk.html`, `finance.html` |
| Blog | `blog.html`, `blog-single.html` |
| Services, Contact | `services.html`, `contact.html` |

## Notes

- Prices/product claims marked `<!-- PLACEHOLDER -->` in HTML are pending client sign-off.
- Social handles in the navbar link to `instagram.com/jozijava`, `facebook.com/jozijava`,
  `tiktok.com/@jozijava`, `linkedin.com/company/jozijava` — **PLACEHOLDER URLs** (LinkedIn
  slug and the TikTok/IG accounts still need client confirmation). Icons are inline SVGs
  (Simple Icons glyphs), so no icon font is required. The footer still carries the
  template's own Twitter/Facebook/Instagram `#` links.
- `product-single.html` is still the template product page (no real Jozi Java roast yet) —
  Add to Cart from the shop cards works regardless.
- Client contact: WhatsApp 27689235818 · info@jozijava.co.za
- Template credit: Colorlib (free-template licence — keep footer credit).

## Live

https://aphiwe91.github.io/jozi-java/
