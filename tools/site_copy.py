"""Remove dash punctuation from customer-facing copy, not URLs or application code."""
import html
import re
from html.parser import HTMLParser


def clean_copy(value):
    # Keep ranges readable instead of joining their endpoints (07:00–17:00, 10–25kg).
    value = re.sub(r'(?<=\d)[\-\u2010-\u2015](?=\d)', ' to ', value)
    value = re.sub(r'[ \t]*[\u2012\u2013][ \t]*', ' to ', value)
    value = re.sub(r'[ \t]*[\u2014\u2015][ \t]*', ', ', value)
    value = re.sub(r'[ \t]+-[ \t]+', ', ', value)
    return re.sub(r'[\-\u2010\u2011]', ' ', value)


def clean_catalogue(catalogue):
    """Keep model IDs, product slugs, photographs and prices completely unchanged."""
    catalogue['notice'] = clean_copy(catalogue['notice'])
    for product in catalogue['products']:
        for key in ('name', 'label', 'notes', 'description', 'brew'):
            product[key] = clean_copy(product[key])
    for equipment in catalogue['equipment']:
        for key in ('name', 'brand', 'detail'):
            equipment[key] = clean_copy(equipment[key])
    return catalogue


class CopyHTML(HTMLParser):
    """Parse text safely; SVG paths, classes, links, data and scripts stay intact."""
    text_attributes = {'alt', 'title', 'placeholder', 'aria-label', 'aria-description'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.raw = 0

    def start_tag(self, tag, attrs, closed=False):
        attrs_map = dict(attrs)
        output = ['<' + tag]
        for key, value in attrs:
            if value is not None:
                is_meta_copy = tag == 'meta' and key == 'content' and (
                    attrs_map.get('name') == 'description' or
                    attrs_map.get('property') in ('og:title', 'og:description'))
                if key in self.text_attributes or is_meta_copy:
                    value = clean_copy(value)
                output.append(' ' + key + '="' + html.escape(value, quote=True) + '"')
            else:
                output.append(' ' + key)
        output.append('/>' if closed else '>')
        self.output.append(''.join(output))

    def handle_starttag(self, tag, attrs):
        self.start_tag(tag, attrs)
        if tag in ('script', 'style'):
            self.raw += 1

    def handle_startendtag(self, tag, attrs):
        self.start_tag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        self.output.append('</' + tag + '>')
        if tag in ('script', 'style'):
            self.raw = max(0, self.raw - 1)

    def handle_data(self, data):
        self.output.append(data if self.raw else html.escape(clean_copy(data), quote=False))

    def handle_decl(self, decl):
        self.output.append('<!' + decl + '>')

    def handle_comment(self, comment):
        self.output.append('<!--' + comment + '-->')


def clean_html_copy(source):
    parser = CopyHTML()
    parser.feed(source)
    parser.close()
    return ''.join(parser.output)
