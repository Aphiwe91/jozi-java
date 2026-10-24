#!/usr/bin/env python3
"""Static QA: generated files, links, anchors, metadata, assets and honest content."""
import json
import re
import subprocess
import sys
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from site_copy import clean_copy, clean_html_copy


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.texts = []
        self.raw_depth = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in ('script', 'style'):
            self.raw_depth += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.raw_depth = max(0, self.raw_depth - 1)

    def handle_data(self, value):
        if not self.raw_depth:
            self.texts.append(value)

    def select(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


class StaticSiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {p.name: Document(p.read_text()) for p in ROOT.glob('*.html')}

    def test_generated_files_are_current(self):
        result = subprocess.run([sys.executable, 'tools/build_site.py', '--check'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_metadata_landmarks_and_ids(self):
        for name, doc in self.pages.items():
            with self.subTest(page=name):
                self.assertEqual(len(doc.select('h1')), 1)
                self.assertEqual(len(doc.select('main')), 1)
                self.assertEqual(len(doc.select('title')), 1)
                self.assertTrue(any(m.get('name') == 'description' and m.get('content') for m in doc.select('meta')))
                self.assertTrue(any(m.get('property') == 'og:image' for m in doc.select('meta')))
                self.assertTrue(any(m.get('rel') == 'canonical' and m.get('href', '').startswith('https://') for m in doc.select('link')))
                ids = [a['id'] for _, a in doc.tags if 'id' in a]
                self.assertEqual(len(ids), len(set(ids)), [i for i, n in Counter(ids).items() if n > 1])
                self.assertTrue(any(a.get('href') == '#main' for a in doc.select('a')))

    def test_local_links_anchors_and_assets(self):
        for name, doc in self.pages.items():
            for tag, attrs in doc.tags:
                for attr in ['href', 'src']:
                    value = attrs.get(attr, '')
                    parts = urlsplit(value)
                    if not value or parts.scheme or parts.netloc:
                        continue
                    path = unquote(parts.path) or name
                    with self.subTest(page=name, target=value):
                        self.assertTrue((ROOT / path).is_file(), f'{name}: missing {value}')
                        self.assertNotEqual(value, '#', f'{name}: inert placeholder link')
                        if attr == 'href' and parts.fragment and path in self.pages:
                            ids = [a.get('id') for _, a in self.pages[path].tags]
                            self.assertIn(parts.fragment, ids)
                for candidate in attrs.get('srcset', '').split(','):
                    if candidate.strip():
                        self.assertTrue((ROOT / candidate.strip().split()[0]).is_file())
                if tag == 'a' and attrs.get('target') == '_blank':
                    self.assertIn('noopener', attrs.get('rel', ''))

    def test_accessible_images_and_fields(self):
        for name, doc in self.pages.items():
            labels = [a.get('for') for a in doc.select('label')]
            for tag, attrs in doc.tags:
                with self.subTest(page=name, tag=tag, id=attrs.get('id')):
                    if tag == 'img':
                        self.assertIn('alt', attrs)
                        self.assertIn('width', attrs)
                        self.assertIn('height', attrs)
                    if tag in ('input', 'select', 'textarea') and attrs.get('type') not in ('radio', 'checkbox', 'hidden'):
                        self.assertTrue(attrs.get('aria-label') or attrs.get('id') in labels)

    def test_no_template_filler_or_external_runtime(self):
        filler = re.compile(r'Far far away|Vokalia|Lorem ipsum|Louise Kelly|Delicious Pizza|John Doe|198 West|17\.5%|same.day.*notified', re.I)
        for name in self.pages:
            with self.subTest(page=name):
                text = (ROOT / name).read_text()
                self.assertIsNone(filler.search(text))
                self.assertNotIn('cdn.tailwindcss', text)
                self.assertNotIn('ftco-loader', text)
                for script in self.pages[name].select('script'):
                    if script.get('src'):
                        self.assertFalse(script['src'].startswith('http'))
                        self.assertIn('defer', script)

    def test_footer_credit_removal(self):
        # The site owner confirmed a licence permitting footer credit removal.
        for name in self.pages:
            with self.subTest(page=name):
                text = (ROOT / name).read_text()
                self.assertNotIn('Original template by', text)
                self.assertNotIn('href="https://colorlib.com"', text)
                self.assertIn('Jozi Java Co (Pty) Ltd.', text)
                self.assertIn('href="privacy.html"', text)

    def test_sitemap_and_price_source(self):
        tree = ElementTree.parse(ROOT / 'sitemap.xml')
        self.assertGreaterEqual(len(tree.findall('{*}url')), 15)
        locations = [e.text for e in tree.findall('.//{*}loc')]
        self.assertFalse(any(Path(urlsplit(u).path).name in ('checkout.html', 'cart.html', '404.html', 'product-single.html') for u in locations))
        catalog = json.loads((ROOT / 'data/catalog.json').read_text())
        self.assertEqual(len(catalog['products']), 3)
        self.assertEqual(len(catalog['equipment']), 17)
        self.assertFalse(catalog['delivery']['confirmed'])
        self.assertIn('preview', catalog['notice'].lower())

    def test_shared_sf_typography(self):
        css = (ROOT / 'css/site.min.css').read_text()
        self.assertIn('"SF Pro Text"', css)
        self.assertIn('"SF Pro Display"', css)
        self.assertIn('"SF Pro"', css)
        self.assertIn('.jj-site *::before', css)
        self.assertNotIn('@font-face', css)
        for name, doc in self.pages.items():
            with self.subTest(page=name):
                styles = [a['href'] for a in doc.select('link') if a.get('rel') == 'stylesheet']
                self.assertEqual(styles, ['css/site.min.css'])

    def test_visible_copy_has_no_dashes(self):
        for name, doc in self.pages.items():
            with self.subTest(page=name):
                self.assertIsNone(re.search(r'[-\u2010-\u2015]', ''.join(doc.texts)))
                for _, attrs in doc.tags:
                    for key in ('alt', 'title', 'aria-label', 'aria-description', 'placeholder'):
                        self.assertIsNone(re.search(r'[-\u2010-\u2015]', attrs.get(key, '')))

    def test_copy_cleanup_preserves_code_and_ranges(self):
        self.assertEqual(clean_copy('Bean-to-cup — 10–25kg, 07:00–17:00'), 'Bean to cup, 10 to 25kg, 07:00 to 17:00')
        source = '<a class="jj-nav-link" href="my-page.html#menu-item" aria-label="Self-service">Bean-to-cup &mdash; 10–25kg</a><svg><path d="M1-2"/></svg><script>var id="my-id";</script><button data-step="-1">&minus;</button>'
        cleaned = clean_html_copy(source)
        self.assertIn('class="jj-nav-link"', cleaned)
        self.assertIn('href="my-page.html#menu-item"', cleaned)
        self.assertIn('aria-label="Self service"', cleaned)
        self.assertIn('Bean to cup, 10 to 25kg', cleaned)
        self.assertIn('d="M1-2"', cleaned)
        self.assertIn('var id="my-id";', cleaned)
        self.assertIn('data-step="-1"', cleaned)
        self.assertIn('−</button>', cleaned)


if __name__ == '__main__':
    unittest.main(verbosity=2)
