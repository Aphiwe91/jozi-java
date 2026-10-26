# Jozi Java — The Coffee Experience

A responsive, static Johannesburg coffee website: beans, commercial equipment,
Piaggio coffee-cart conversions, business enquiries and WhatsApp ordering.

## Preview

```bash
python3 -m http.server 8002 --bind ::
```

Open **http://localhost:8002/**. Ports 8000 and 8001 belong to other projects.
Generated root HTML is committed, so hosting needs no Python server, build system,
database or third-party JavaScript service. Relative links work on GitHub Pages.

## Editing and building

```bash
python3 tools/optimize_images.py  # only needed after adding/changing client photos
python3 tools/build_site.py
python3 tools/build_site.py --check
```

Python 3 and Pillow are required for local generation. There is no npm dependency.

| Source | Purpose |
|---|---|
| `pages/*.html` | Page content; edit these rather than the generated root HTML |
| `templates/base.html` | Shared accessible header, navigation, footer, metadata |
| `templates/product.html` | Dedicated roast detail pages |
| `data/pages.json` | Page titles, descriptions, navigation and script configuration |
| `data/catalog.json` | Single source for the three roasts, 17 equipment entries and preview shipping rates |
| `css/base.css`, `css/pages.css`, `css/refresh.css` | Foundations, structural layouts and the current Mint-inspired preview design |
| `js/cart.js` | Validated cart, quantities, explicit grind choice, checkout and WhatsApp order preparation |
| `js/site.js` | Mobile navigation, equipment filters, enquiry forms, deposit/build planners, journal filters and opt-in map |
| `js/shop.js` | Instant search, `?q=` search, sorting and empty states |
| `js/home.js` | Five home slides and three category carousels, each on a 10-second cycle; pause/manual controls; stable story typing |

### Current design direction — local preview, not yet approved for publishing

The owner requested a new direction inspired by `https://za.mintgroup.net/`, with a
local preview before any GitHub push. The reference homepage, about page and
services page informed the clear navigation, strong photographic opening, open
service pathways, generous whitespace, alternating light/dark sections and clear
contact prompts. No Mint artwork, logos, videos, copy or runtime code is reused.

`css/refresh.css` is a final, shared design layer compiled into `css/site.min.css`.
It uses Jozi Java's own photography, warm cream surfaces and The Wilds Roast's green palette,
native SF typography and responsive layouts throughout. The 55%-opacity navbar,
60%-opacity full-width welcome image, existing headline, business details, product
data and cart/enquiry behaviour are retained. The old structural stylesheet stays
available underneath the refresh; the previous published design is in git history.
The equipment catalogue remains a working specification/price table. The announcement
belt above the navbar has been removed; navigation starts at the top of the page.

### The Wilds Roast colour theme

The green palette is sampled from the catalogue's Wilds Roast photograph,
`images/jozi/jozi-03.jpeg`: sage `#98b176`, with dark olive `#4d6b33` and moss
`#344c22` companions for readable text and buttons. Shared tokens in `css/refresh.css`
carry the theme through buttons, links, icons, selected options, focus and hover
states, banners, forms, the cart, dark feature sections and footer. Product photos
and catalogue data are not recoloured or changed. This is a photographic colour
reference, not a claim to an official print colour specification.

The restored homepage contact form uses the same working WhatsApp preparation and
consent handling as the contact page. Fake testimonials, invented discounts and
dead template links were not brought back with the previous look.

### Interaction details

The refresh includes button lifts and arrow feedback, raised service/product cards,
subtle image zoom, equipment-row highlighting, navigation underlines and footer-link
feedback. Keyboard focus gets equivalent highlights and visible outlines. All actions
and information remain available without hovering. Moving effects only apply to a
fine pointer that supports hover and when reduced motion is not requested; touch
and reduced-motion users keep the static layout and usable controls. Hero image
opacity, navbar opacity, SF typography and the removed announcement belt are unchanged.

### Typography — Apple SF family throughout

`--jj-font` in `css/base.css` is the only active font-family stack. It applies to
all site text, headings, navigation, prices, form controls, generated labels and
message previews (including `pre`/`code`, which otherwise default to monospace).
Locally installed `SF Pro Text`, `SF Pro Display` and `SF Pro` are prioritised
explicitly, followed by `-apple-system` / `BlinkMacSystemFont` for native San Francisco
on Apple devices. Other platforms without SF use a system sans-serif fallback.
Automatic optical sizing and native font smoothing are enabled. Apple's proprietary
font binaries are not bundled, downloaded
from an unofficial CDN or redistributed. The inline SVG icons are unaffected.

### Website copy — no dash punctuation

The build removes hyphens and dash separators from displayed copy, metadata,
labels and published catalogue descriptions through `tools/site_copy.py`. Number
and time ranges use “to”; compound words use spaces. Links, filenames, CSS classes,
model IDs, SVG paths, scripts and the mathematical quantity-minus control are not
altered. Dynamic site messages follow the same convention. Visitor-entered names,
addresses, notes and search text are preserved, not silently rewritten.

Generated assets: root HTML, `css/site.min.css`, `js/catalog.js`, `sitemap.xml`,
`robots.txt` and responsive files in `images/optimized/`. Client originals remain
untouched in `images/jozi/`. Derivatives preserve aspect ratios, do not upscale small
originals, and remove embedded metadata. Original Colorlib CSS, scripts and fonts
remain available for reference, but **are not loaded by the finished pages**.

The default canonical site is `https://aphiwe91.github.io/jozi-java/`. On a domain
cutover, rebuild with the confirmed live origin:

```bash
JJ_SITE_URL=https://jozijava.co.za/ python3 tools/build_site.py
```

Do not change canonical URLs to a domain until it actually serves this build.
The legacy `product-single.html` remains a usable, noindexed Wilds Roast page;
the three real roast pages have their own URLs. `404.html` supports GitHub Pages.

## What works now

- All 23 pages share the same navigation, footer, responsive layout and SEO basics.
- Coffee search/sort, dedicated roast pages, bag-size prices, required grind choice,
  persistent cart, quantity controls, delivery/collection and empty states.
- Stored cart data is treated as untrusted: invalid entries are dropped; names,
  images and prices are refreshed from the catalogue; quantities are bounded.
- Contact, wholesale and finance forms prepare complete WhatsApp messages with
  required consent, review text and a visible retry link. **They do not email, save
  enquiries to a CRM or falsely report that a message was received.**
- The equipment catalogue combines setup, brand, budget and text filters. Quote
  links carry the selected model to contact; finance links carry the model/value.
- The finance page computes a deposit and remaining asset value, checks the three
  published CCS starting criteria and links to the official CCS rental calculator.
  No guessed interest rate, credit approval or guaranteed ownership claim.
- The Tuk Tuk planner prepares a structured build brief and calculates only known
  equipment prices. Vehicle/conversion pricing is not double-counted into a false
  all-in quote.
- Keyboard navigation, skip link, native FAQs, labelled fields, live announcements,
  mobile menu Escape handling and reduced-motion support. Static content/navigation
  stays visible without JavaScript. Maps connect to Google only after a click.
- All third-party runtime dependencies, Google Fonts requests, blocking loaders,
  fake testimonials, dummy comments and dead template links are removed from pages.
- Responsive WebP images, lazy below-fold media, intrinsic dimensions, deferred
  scripts, canonical/social metadata, structured data and a sitemap.

## Ordering and privacy

WhatsApp Business: **27689235818** · **info@jozijava.co.za**.

The cart is stored as `jj_cart_v1`. Checkout **prepares** an order request; the
customer must press Send in WhatsApp and Jozi Java must confirm price/stock/payment.
No money is taken online. Opening WhatsApp is not proof of sending, so the cart is
kept until the customer explicitly empties it. A blocked popup retains a retry link.

Contact/delivery details are saved as `jj_customer_v1` **only with the optional
remember-details checkbox**. “Forget any saved details” removes that browser copy.
Enquiry forms do not persist personal or finance information locally. There are no
marketing pixels or automatic newsletter signups. `privacy.html` describes the
website's actual behaviour; it is not a claim of audited POPIA compliance.

## Client approvals / remaining launch integrations

The frontend is ready to review. It is **not an automated paid e-commerce platform**.

- **Bean prices:** all existing R45/49/52 starting prices and size prices are preview
  placeholders, carried forward rather than presented as approved retail prices.
- **Courier:** R75 / free from R500 is unconfirmed. Review coverage and lead times.
- **Equipment:** guide prices are from the website brief. Current stock, retail
  margins, manufacturer specs, warranties and installation scope need approval.
- **Piaggio:** January 2026 references are not a current all-inclusive build quote.
  Confirm build tiers, prices and exactly what each vehicle/build price includes.
- **Café menu:** no approved food/drinks price list was supplied. The page directs
  visitors to the team for the current location menu instead of publishing fake dishes.
- **Subscriptions:** regular-order enquiries only. No approved discount, recurring
  billing, customer account or self-service pause/cancel system exists yet.
- **Wholesale:** confirm pricing tiers, MOQs, lead times and trade account terms.
  No unapproved customer endorsement (for example FSC) is published.
- **Payments/CMS/CRM:** select and integrate the production commerce/payment and
  enquiry services before advertising automated sales or subscriptions.
- **Legal/business:** approve privacy/retention arrangements, Information Officer
  details, returns policy, registration/VAT disclosures and order terms.
- **Locations:** Roastery address/hours follow the existing home page. Confirm all
  exact addresses, map pins, visitor access and individual coffee-bar hours.
- **Social:** Instagram/Facebook/TikTok handles follow the brief; confirm ownership.
  The unconfirmed LinkedIn slug was not carried into the new shared navigation.
- **Photos:** identify/approve exact roast packaging shots and customer build photos.
  Only named equipment photos are assigned to models; absent photos are honestly
  labelled instead of showing the wrong machine. Individual conversion photos are
  not assigned unverified customer names.
- **Domain/analytics:** confirm the live domain, hosting and Search Console. Add
  analytics only with an appropriate privacy review; none is installed by default.

CCS: `https://ccs.equipment/#calculator`; formal applications at
`https://ccs.equipment/rental-application-form/` (NCRCP13995). No iframe/prefill
integration or automated handoff is assumed without agreement with CCS.

## Tests

```bash
python3 tests/static_test.py
python3 tests/cart_test.py
python3 tests/site_test.py
xvfb-run -a python3 tests/hover_test.py  # real mouse, keyboard, touch and reduced motion
python3 tests/accessibility_test.py /path/to/axe.min.js  # optional axe-core audit
```

Browser tests need the :8002 server, Selenium, `/usr/bin/chromium` and
`/usr/bin/chromedriver`. They explicitly configure the driver rather than relying
on Selenium Manager. Site QA checks all pages at 320, 390, 768 and 1440px, browser
errors, images, interactions, restoration-specific design checks and no-JavaScript behaviour. Screenshots go to
`/tmp/opencode/jozi-java/`, not the repository. Automated accessibility checks do not
replace assistive-technology review.

The site owner confirmed a licence permitting removal of the Colorlib footer
attribution. The visible credit is omitted on that basis; existing third-party
licence notices remain unchanged. Real business documents outside this website
directory stay local and are not part of this project or deployment.
