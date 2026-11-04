"""Check links, bilingual pairing, published works and structured facts.

Usage: python tools/verify_brand.py [--url http://127.0.0.1:52907/]
"""
import argparse
import json
import re
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from urllib.request import urlopen
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE='https://miaomeihuamu.com'

class Page(HTMLParser):
    def __init__(self,source):
        super().__init__()
        self.tags=[];self.ids=[];self.words=[];self.ignore=0
        self.feed(source)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);self.tags.append((tag,attrs))
        if attrs.get('id'):self.ids.append(attrs['id'])
        if tag in ('script','style'):self.ignore+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.ignore-=1
    def handle_data(self,data):
        if not self.ignore:self.words.append(data)

def disk(path):
    p=ROOT/unquote(path.lstrip('/'))
    return p/'index.html' if p.is_dir() or path.endswith('/') else p

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url')
    args=parser.parse_args()
    routes=json.loads((ROOT/'content/brand/routes.json').read_text(encoding='utf-8'))
    sources={route:disk(route).read_text(encoding='utf-8') for route in routes}
    pages={route:Page(source) for route,source in sources.items()}
    errors=[];links_checked=0;json_count=0;faq_count=0
    def check(value,message):
        if not value:errors.append(message)
    for route,p in pages.items():
        source=sources[route]
        lang=next(a.get('lang') for t,a in p.tags if t=='html')
        check(lang==('en' if route.startswith('/en/') else 'zh-CN'),route+' language')
        check(sum(t=='h1' for t,a in p.tags)==1,route+' h1 count')
        check(len(p.ids)==len(set(p.ids)),route+' duplicate IDs')
        check(bool(re.search(r'<meta name="description" content="[^"]{30,}"',source)),route+' empty/short description')
        canonical=[a['href'] for t,a in p.tags if t=='link' and a.get('rel')=='canonical']
        check(canonical==[BASE+route],route+' canonical')
        alts={a['hreflang']:a['href'] for t,a in p.tags if t=='link' and 'hreflang' in a}
        check(set(alts)=={'zh-CN','en','x-default'},route+' language alternatives')
        other='zh-CN' if lang=='en' else 'en'
        switch=[a['href'] for t,a in p.tags if t=='a' and a.get('class')=='language-switch']
        check(switch==[alts.get(other,'').removeprefix(BASE)],route+' language switch target')
        other_path=alts.get(other,'').removeprefix(BASE)
        if other_path in pages:
            reciprocal={a['hreflang']:a['href'] for t,a in pages[other_path].tags if t=='link' and 'hreflang' in a}
            check(reciprocal.get(lang)==BASE+route,route+' reciprocal hreflang')
        else:check(False,route+' missing translated page')
        for tag,attrs in p.tags:
            for attr in ('href','src','poster'):
                value=attrs.get(attr)
                if not value:continue
                u=urlsplit(value)
                if u.scheme or u.netloc:continue
                path=u.path or route
                if not path.startswith('/'):
                    # Generated pages deliberately use root-relative links.
                    from urllib.parse import urljoin
                    path=urlsplit(urljoin(BASE+route,value)).path
                target=disk(path)
                check(target.is_file(),f'{route}: missing {value}')
                if target.is_file() and target.suffix=='.html' and u.fragment:
                    target_page=pages.get(path) or Page(target.read_text(encoding='utf-8'))
                    check(unquote(u.fragment) in target_page.ids,f'{route}: missing anchor {value}')
                links_checked+=1
            if tag=='img' and attrs.get('src'):check(bool(attrs.get('alt')),route+' image alt')
            if tag=='video':check('autoplay' not in attrs and attrs.get('preload')=='none',route+' video preload')
        visible=''.join(p.words)
        for forbidden in ('English-speaking','we speak English','two clients a day','One free touch-up','每天只预约两位','游泳运动都不影响','无痛感','江浙沪'):
            check(forbidden not in source,route+' stale claim: '+forbidden)
        check(not re.search(r'(?:¥|￥|RMB|CNY)\s*\d|\d+\s*元',visible),route+' numeric price')
        schemas=[json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>',source,re.S)]
        json_count+=len(schemas)
        for schema in schemas:
            if schema.get('@type')=='FAQPage':
                questions=[(q['name'],q['acceptedAnswer']['text']) for q in schema['mainEntity']]
                rendered=re.findall(r'<details class="faq"><summary>(.*?)</summary><p>(.*?)</p></details>',source,re.S)
                import html
                check(questions==[(html.unescape(q),html.unescape(a)) for q,a in rendered],route+' FAQ mismatch')
                faq_count+=len(questions)
            if schema.get('@type') in ('LocalBusiness','BeautySalon'):
                check(schema['telephone']=='19282182068' and schema['url']==BASE+'/',route+' business identity')
                check('availableLanguage' not in schema,route+' unverified reception language')
            if schema.get('@type')=='HowTo':
                check(len(schema['step'])==9,route+' nine design steps')
                for step in schema['step']:check(step['name'] in visible and step['text'] in visible,route+' HowTo content mismatch')
    published=[];private=[]
    for file in (ROOT/'content/works').glob('*.json'):
        for row in json.loads(file.read_text(encoding='utf-8')):
            media=row.get('image') or row.get('video')
            if media:(published if row.get('published') else private).append(media)
    for route in ('/works.html','/en/works.html'):
        source=sources[route]
        for media in published:check(media in source,route+' missing published record '+media)
        for media in private:check(media not in source,route+' private record exposed '+media)
        schemas=[json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>',source,re.S)]
        collection=next(s for s in schemas if s['@type']=='CollectionPage')
        actual=[i['item']['contentUrl'].removeprefix(BASE) for i in collection['mainEntity']['itemListElement']]
        check(Counter(actual)==Counter(published),route+' work schema mismatch')
    before_sitemap=subprocess.check_output(['git','show','d75e0d9:sitemap.xml'],cwd=ROOT).decode('utf-8')
    namespace={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    old={n.text for n in ET.fromstring(before_sitemap).findall('.//s:loc',namespace)}
    new={n.text for n in ET.parse(ROOT/'sitemap.xml').findall('.//s:loc',namespace)}
    check(old<=new,'existing sitemap URLs removed')
    check({BASE+r for r in routes}<=new,'generated page missing from sitemap')
    metadata=json.loads((ROOT/'content/brand/original-metadata.json').read_text(encoding='utf-8'))
    for route,p in pages.items():
        old_ids=metadata.get(disk(route).relative_to(ROOT).as_posix(),{}).get('ids',[])
        check(set(old_ids)<=set(p.ids),route+' original anchor removed')
    http=[]
    if args.url:
        def fetch(route):
            with urlopen(args.url.rstrip('/')+route,timeout=15) as response:
                return {'path':route,'status':response.status,'size':len(response.read()),'noindex':response.headers.get('X-Robots-Tag')}
        with ThreadPoolExecutor(max_workers=6) as pool:http=list(pool.map(fetch,routes))
        check(all(r['status']==200 for r in http),'HTTP route failure')
    result={'status':'FAIL' if errors else 'PASS','pages':len(routes),'local_links_and_assets':links_checked,'json_ld_blocks':json_count,'faq_matches':faq_count,'published_work_records':len(published),'private_records_excluded':len(private),'existing_sitemap_urls_preserved':len(old),'http_pages':len(http),'errors':errors,'http':http}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
