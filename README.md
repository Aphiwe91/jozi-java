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
- `js/shop.js` — collection sorting + size-pill price swap (presentation only)
- `images/jozi/jozi-01..47.jpeg` — client photos

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
- Cart/checkout pages are still template-level — no cart logic wired yet.
- Client contact: WhatsApp 27689235818 · info@jozijava.co.za
- Template credit: Colorlib (free-template licence — keep footer credit).

## Live

https://aphiwe91.github.io/jozi-java/
