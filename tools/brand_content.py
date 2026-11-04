"""Bilingual editorial source loaded from owner-managed CMS JSON.

Each article retains its existing URL. Both language editions use the same
record, while each language has its own editable text fields.
No runtime dependencies are required.
"""
from cms_content import ROOT, load

BRAND = '描眉画目·定制美学'
BRAND_EN = 'Miaomeihuamu · Bespoke Aesthetics'

def pairs(name, with_id=False):
    keys = (['id'] if with_id else []) + ['title', 'title_en', 'description', 'description_en']
    return [tuple(row.get(key, '') for key in keys) for row in load(name + '.json', list)]

DESIGN = pairs('design')
SERVICES = pairs('services', True)
FAQ = pairs('faq')
ARTICLES = []
for path in sorted((ROOT / 'content/articles').glob('*.json')):
    row = load('articles/' + path.name)
    ARTICLES.append({
        'slug': row['slug'],
        'title': [row['title'], row['title_en']],
        'intro': [row['intro'], row['intro_en']],
        'sections': [tuple(s.get(k, '') for k in ('title', 'title_en', 'description', 'description_en')) for s in row['sections']],
        'section_images': [s.get('image') or '' for s in row['sections']],
    })
