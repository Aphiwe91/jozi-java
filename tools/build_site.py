#!/usr/bin/env python3
"""Build the static site with shared navigation, product data and SEO.

Edit pages/, templates/ and data/ rather than the generated root HTML.
Run python3 tools/optimize_images.py once if new photographs are added.
Requires Pillow for image dimensions (already installed locally).
"""
import argparse
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode
from xml.sax.saxutils import escape as xml_escape
from site_copy import clean_copy, clean_catalogue, clean_html_copy

ROOT = Path(__file__).resolve().parents[1]
SITE = os.environ.get("JJ_SITE_URL", "https://aphiwe91.github.io/jozi-java/").rstrip("/") + "/"
CATALOG = clean_catalogue(json.loads((ROOT / "data/catalog.json").read_text()))
PAGES = json.loads((ROOT / "data/pages.json").read_text())
for page in PAGES.values():
    for field in ('title', 'description', 'heading'):
        if field in page:
            page[field] = clean_copy(page[field])
NAV = [("index", "Home"), ("equipment", "Equipment"), ("tuktuk", "Tuk Tuk"), ("shop", "Shop"), ("about", "Our Story"), ("menu", "Café & Menu"), ("finance", "Finance"), ("blog", "Blog"), ("contact", "Contact")]


def esc(value):
    return html.escape(str(value), quote=True)


def money(value):
    return f"R{value:,.2f}"


def image(name, alt, cls="", size=960, eager=False):
    stem = Path(name).stem
    from PIL import Image  # already available locally; only used for intrinsic dimensions
    with Image.open(ROOT / "images/jozi" / name) as im:
        width, height = im.size
    return (f'<img src="images/optimized/{stem}-{size}.webp" '
            f'srcset="images/optimized/{stem}-480.webp {min(480, width)}w, images/optimized/{stem}-960.webp {min(960, width)}w" '
            f'sizes="(max-width: 767px) 100vw, 50vw" width="{width}" height="{height}" '
            f'alt="{esc(alt)}" class="{cls}" decoding="async" '
            + ('fetchpriority="high"' if eager else 'loading="lazy"') + '>')


def product_card(p, index=0):
    prices = esc(json.dumps(p["prices"], separators=(",", ":")))
    size_buttons = ''.join(f'<button type="button" class="jj-size" aria-pressed="false">{s}</button>' for s in p["prices"])
    return f'''<div class="jj-card-wrap" data-featured="{index}" data-price="{min(p['prices'].values())}" data-name="{esc(p['name'])}">
      <article class="jj-card" data-sku="{p['sku']}" data-name="{esc(p['name'])}" data-img="images/optimized/{Path(p['image']).stem}-480.webp">
        <a href="{p['slug']}.html" class="jj-product-image" aria-label="Explore {esc(p['name'])}">{image(p['image'], p['name'] + ' packaging', size=480)}</a>
        <div class="jj-card-body"><span class="jj-eyebrow">{esc(p['label'])}</span><h3><a href="{p['slug']}.html">{esc(p['name'])}</a></h3>
          <p class="jj-card-notes">{esc(p['notes'])}</p><p class="jj-small">Whole bean or ground for your brew method.</p>
          <div class="jj-sizes" role="group" aria-label="Bag size for {esc(p['name'])}" data-prices="{prices}">{size_buttons}</div>
          <label class="sr-only" for="grind-{index}">Choose a grind for {esc(p['name'])}</label><select id="grind-{index}" class="jj-grind form-control" aria-label="Choose a grind for {esc(p['name'])}"><option value="">Choose grind…</option></select>
          <p class="jj-card-price jj-price"><span>from {money(min(p['prices'].values()))}</span></p><button type="button" class="btn btn-primary jj-add">Add to cart <span aria-hidden="true">+</span></button>
        </div>
      </article></div>'''


def equipment_cards():
    labels = {"barista": "Barista-staffed", "automatic": "Bean-to-cup", "grinder": "Grinder", "roaster": "Roaster"}
    out = []
    for e in CATALOG["equipment"]:
        params = urlencode({"topic": "Equipment", "message": "I'd like a quote and specification sheet for " + e["name"] + "."})
        finance = urlencode({"asset": e["name"], "value": e["price"]})
        photo = image(e["image"], e["name"], cls="jj-equipment-thumb", size=480) if e.get("image") else ''
        out.append(f'''<tr class="jj-equipment-card" id="{e['id']}" data-kind="{e['kind']}" data-brand="{esc(e['brand'])}" data-price="{e['price']}">
          <th scope="row"><span class="jj-equipment-type">{labels[e['kind']]}</span>{esc(e['name'])}{photo}</th>
          <td class="jj-equipment-description">{esc(e['detail'])}</td><td class="jj-equipment-price">{money(e['price'])}</td>
          <td><div class="jj-actions"><a class="btn btn-primary" href="contact.html?{esc(params)}#enquiry">Request Quote</a><a class="jj-text-link" href="finance.html?{esc(finance)}#calculator">Finance</a></div></td></tr>''')
    return '<table class="jj-equipment-table"><caption class="sr-only">Coffee equipment guide prices, including VAT. Confirm current prices and specifications before ordering.</caption><thead><tr><th scope="col">Model</th><th scope="col">Description</th><th scope="col">Incl. VAT</th><th scope="col">Enquiries</th></tr></thead><tbody>' + '\n'.join(out) + '</tbody></table>'


def page_banner(meta):
    heading = esc(meta.get('heading', meta['title'].split(' | ')[0]))
    classes = 'jj-page-hero jj-article-banner' if meta.get('article') else 'jj-page-hero'
    trail = '<span>/</span><a href="blog.html">Blog</a>' if meta.get('article') else ''
    return f'<header class="{classes}"><div class="container"><div class="jj-banner-text"><h1>{heading}</h1><div class="jj-breadcrumb"><a href="index.html">Home</a>{trail}<span>/</span><span>{heading}</span></div></div></div></header>'


def featured_equipment():
    out = []
    for e in CATALOG['equipment']:
        if e['id'] not in ('casadio-2', 'buddy'):
            continue
        out.append(f'<article><a href="equipment.html#{e["id"]}">{image(e["image"], e["name"], size=480)}</a><h3><a href="equipment.html#{e["id"]}">{esc(e["name"])}</a></h3><p class="price">{money(e["price"])}</p><a class="btn btn-primary" href="equipment.html#{e["id"]}">View Equipment</a></article>')
    return '\n'.join(out)


def home_coffee():
    out = []
    for p in CATALOG['products']:
        out.append(f'<article><a href="{p["slug"]}.html">{image(p["image"], p["name"] + " packaging", size=480)}</a><h3><a href="{p["slug"]}.html">{esc(p["name"])}</a></h3><p>Whole bean or ground<br>1kg guide price: {money(p["prices"]["1kg"])}</p><a class="btn btn-primary" href="{p["slug"]}.html">Shop</a></article>')
    out.append('<article><a href="shop.html#regular-orders">' + image('jozi-20.jpeg', 'Coffee at Jozi Java', size=480) + '</a><h3>Coffee Subscriptions</h3><p>Weekly, fortnightly or monthly supplies arranged directly with our team.</p><a class="btn btn-primary" href="shop.html#regular-orders">Enquire</a></article>')
    return '\n'.join(out)


def render_tokens(text, values):
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: str(values[match[1]]), text)


def build():
    outputs = {}
    base = (ROOT / "templates/base.html").read_text()
    products_markup = '\n'.join(product_card(p, i) for i, p in enumerate(CATALOG["products"]))
    equipment_markup = equipment_cards()
    for key, meta in PAGES.items():
        source = (ROOT / "pages" / f"{meta.get('source', key)}.html").read_text()
        content = render_tokens(source, {
            "PRODUCT_CARDS": products_markup,
            "EQUIPMENT_CARDS": equipment_markup,
            "FEATURED_EQUIPMENT": featured_equipment(),
            "HOME_COFFEE": home_coffee(),
            "PAGE_BANNER": page_banner(meta),
            "PRICE_NOTICE": esc(CATALOG["notice"])
        })
        outputs[key + '.html'] = (content, meta)
    product_template = (ROOT / "templates/product.html").read_text()
    for p in CATALOG["products"]:
        params = urlencode({"topic": "Coffee subscription", "message": "I'd like to discuss a regular order of " + p["name"] + "."})
        content = render_tokens(product_template, {
            "NAME": esc(p["name"]), "SKU": p["sku"], "IMAGE": image(p["image"], p["name"] + " packaging", eager=True),
            "IMAGE_URL": "images/optimized/" + Path(p["image"]).stem + "-480.webp",
            "LABEL": esc(p["label"]), "NOTES": esc(p["notes"]), "DESCRIPTION": esc(p["description"]), "BREW": esc(p["brew"]),
            "PRICES": esc(json.dumps(p["prices"])), "MIN_PRICE": money(min(p["prices"].values())),
            "SIZES": ''.join(f'<button type="button" class="jj-size" aria-pressed="false">{s}</button>' for s in p["prices"]),
            "SUBSCRIPTION_LINK": "contact.html?" + esc(params) + "#enquiry", "PRICE_NOTICE": esc(CATALOG["notice"]),
            "PRODUCT_CARDS": '\n'.join(product_card(other, i) for i, other in enumerate(CATALOG["products"]) if other != p)
        })
        meta = {"title": p["name"] + " — Coffee Beans | Jozi Java", "description": p["description"], "nav": "shop", "image": p["image"], "product": p}
        outputs[p["slug"] + '.html'] = (content, meta)
    # Retain the template-era URL without duplicating its search listing.
    content, meta = outputs['the-wilds-roast.html']
    outputs['product-single.html'] = (content, dict(meta, canonical='the-wilds-roast.html', noindex=True))

    rendered = {}
    for name, (content, meta) in outputs.items():
        key = name[:-5]
        active = meta.get("nav", key)
        nav_items = []
        for slug, label in NAV:
            active_class = ' active' if slug == active else ''
            current = ' aria-current="page"' if slug == active else ''
            nav_items.append(f'<li class="nav-item{active_class}"><a class="nav-link" href="{slug}.html"{current}>{label}</a></li>')
        nav = ''.join(nav_items)
        nav += '<li class="nav-item jj-nav-cart"><a class="nav-link" href="cart.html"' + (' aria-current="page"' if active == 'cart' else '') + '>Cart <span class="jj-cart-badge" hidden></span></a></li>'
        canonical = SITE + meta.get("canonical", name)
        schema = {"@context": "https://schema.org", "@type": "WebPage", "name": meta["title"], "description": meta["description"], "url": canonical, "inLanguage": "en-ZA"}
        if meta.get('product'):
            p = meta['product']
            # Deliberately no Offer: prices are unconfirmed, not crawlable retail promises.
            schema = {"@context": "https://schema.org", "@type": "Product", "name": p['name'], "description": p['description'], "sku": p['sku'], "brand": {"@type": "Brand", "name": "Jozi Java"}, "image": SITE + 'images/optimized/' + Path(p['image']).stem + '-960.webp'}
        if key == 'index':
            schema = {"@context": "https://schema.org", "@type": "Organization", "name": "Jozi Java Co (Pty) Ltd", "url": SITE, "logo": SITE + 'images/optimized/jozi-logo-320.webp', "email": "info@jozijava.co.za", "telephone": "+27689235818", "address": {"@type": "PostalAddress", "streetAddress": "2 Honeyguide, Douglasdale", "addressLocality": "Johannesburg", "addressCountry": "ZA"}}
        rendered[name] = render_tokens(base, {
            "TITLE": esc(meta["title"]), "DESCRIPTION": esc(meta["description"]), "CANONICAL": esc(canonical),
            "ROBOTS": "noindex, follow" if meta.get('noindex') else "index, follow", "OG_TYPE": "article" if meta.get('article') else "website",
            "SHARE_IMAGE": SITE + 'images/optimized/' + Path(meta.get('image', 'jozi-09.jpeg')).stem + '-960.webp',
            "PRELOAD": '<link rel="preload" as="image" href="images/optimized/jozi-06-960.webp">' if key == 'index' else '',
            "SCHEMA": '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>',
            "NAV": nav, "CONTENT": content, "BODY_CLASS": 'jj-home' if key == 'index' else 'jj-inner',
            "SCRIPTS": ''.join(f'<script defer src="js/{s}.js"></script>' for s in meta.get('scripts', []))
        })
        rendered[name] = re.sub(r'[ \t]+$', '', clean_html_copy(rendered[name]), flags=re.M)
    css = '\n'.join((ROOT / 'css' / n).read_text() for n in ['base.css', 'pages.css'])
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    rendered['css/site.min.css'] = re.sub(r'\n\s*', '\n', css).strip() + '\n'
    rendered['js/catalog.js'] = '/* Generated by tools/build_site.py; edit data/catalog.json. */\nwindow.JoziCatalog = ' + json.dumps(CATALOG, ensure_ascii=False, separators=(',', ':')) + ';\n'
    urls = [SITE + name for name, (_, meta) in outputs.items() if not meta.get('noindex')]
    rendered['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join('<url><loc>' + xml_escape(u) + '</loc></url>\n' for u in urls) + '</urlset>\n'
    rendered['robots.txt'] = 'User-agent: *\nAllow: /\nSitemap: ' + SITE + 'sitemap.xml\n'
    return rendered


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if generated files are stale; do not write.')
    args = parser.parse_args()
    stale = []
    for name, contents in build().items():
        target = ROOT / name
        if not target.exists() or target.read_text() != contents:
            stale.append(name)
            if not args.check:
                target.write_text(contents)
    if args.check and stale:
        raise SystemExit('Generated files need rebuilding: ' + ', '.join(stale))
    print(('Checked' if args.check else 'Built') + ' static pages, catalogue, CSS and sitemap.' + (f' Updated {len(stale)} files.' if not args.check else ''))
