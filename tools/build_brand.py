"""Build the bilingual static pages using existing assets and the phase-one shell.

Run: python tools/build_brand.py
No network, package installation or deployment is performed.
"""
import copy
import html
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from brand_content import BRAND, BRAND_EN, DESIGN, SERVICES, FAQ, ARTICLES
from cms_content import load, validate, CATEGORIES, work_records, selection
from package_site import release_metadata

HOME = load('home.json')
STUDIO = load('studio.json')
WORKS_PAGE = load('works-page.json')

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://miaomeihuamu.com'
BASELINE = 'd75e0d9'
try:
    DATE = os.environ.get('CMS_CONTENT_DATE') or subprocess.check_output(['git','log','-1','--format=%cs'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
except (OSError, subprocess.CalledProcessError):
    DATE = datetime.now(timezone.utc).date().isoformat()
DIANPING = 'https://www.dianping.com/shop/ka17X0dd6YqQIfYc'
MAP = 'https://map.baidu.com/bdpoiwise/index.html?uid=e14d4f6c79332f56a7c756d2'
METADATA = ROOT / 'content/brand/original-metadata.json'

def e(value):
    return html.escape(str(value), quote=True)

def text(zh, en, lang):
    return en if lang else zh

def route(key, lang=0):
    if key == 'home': return '/en/' if lang else '/'
    if key == 'posts': return '/en/posts/' if lang else '/posts/'
    if key == 'guide': return '/en/eyebrow-tattoo-shanghai-guide.html' if lang else '/posts/eyebrow-tattoo-shanghai-guide.html'
    return ('/en/' if lang else '/') + key

def article_route(slug, lang):
    return route('guide',lang) if slug == 'eyebrow-tattoo-shanghai-guide' else route('posts/'+slug+'.html',lang)

def disk(path):
    return ROOT / (path.lstrip('/') + ('index.html' if path.endswith('/') else ''))

def original(path):
    result = subprocess.run(['git','show',BASELINE+':'+path],cwd=ROOT,capture_output=True)
    return result.stdout.decode('utf-8') if result.returncode == 0 else ''

if not METADATA.exists():
    originals = {}
    names = subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=ROOT,text=True).splitlines()
    for name in names:
        if name.endswith('.html') and not name.startswith(('admin/','preview/')):
            source = original(name)
            schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>',source,re.S)]
            schemas = [s if name == 'index.html' else {k:v for k,v in s.items() if k in ('@context','@type','datePublished','dateCreated','image','thumbnailUrl','license')} for s in schemas if (name == 'index.html' and s.get('@type') in ('LocalBusiness','Person','VideoObject')) or s.get('@type') == 'Article']
            originals[name] = {'schemas':schemas,'ids':re.findall(r'\bid="([^"]+)"',source)}
    METADATA.parent.mkdir(parents=True,exist_ok=True)
    METADATA.write_text(json.dumps(originals,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ORIGINALS = json.loads(METADATA.read_text(encoding='utf-8'))
HOME_SCHEMAS = ORIGINALS['index.html']['schemas']
BUSINESS = copy.deepcopy(next(s for s in HOME_SCHEMAS if s['@type']=='LocalBusiness'))
BUSINESS['name'] = BRAND
if 'Miaomeihuamu Bespoke Aesthetics' not in BUSINESS['alternateName']:
    BUSINESS['alternateName'].append('Miaomeihuamu Bespoke Aesthetics')
BUSINESS['description'] = HOME['hero_intro']
PERSON = next(s for s in HOME_SCHEMAS if s['@type']=='Person')
VIDEO = next(s for s in HOME_SCHEMAS if s['@type']=='VideoObject')

DIMENSIONS = {'assets/hero-model.webp':(702,996), 'assets/env/window.jpg':(810,1216),
 'assets/case-d-white-clip.webp':(600,900),
 'assets/uploads/images/imported/men-brow/03.jpg':(1179,1129),
 'assets/works/women-brow-direction-detail.png':(867,1156),'assets/works/women-brow-arch-detail.jpg':(1079,1293),
 'assets/uploads/images/confirmed/case-d-white-clip.png':(750,1125),'assets/uploads/images/imported/women-brow/07.jpg':(1080,1620),
 'assets/wechat-miaomeihuamu.jpg':(960,960)}

def image(src, alt, css='', eager=False, img_id=''):
    size = DIMENSIONS.get(src.lstrip('/'))
    dimensions = f' width="{size[0]}" height="{size[1]}"' if size else ''
    identity = f' id="{e(img_id)}"' if img_id else ''
    loading = ' fetchpriority="high"' if eager else ' loading="lazy"'
    return f'<img src="/{e(src.lstrip("/"))}" alt="{e(alt)}" class="{e(css)}"{identity}{dimensions}{loading}>'

def button(label, lang, secondary=False):
    return f'<a class="{"text-link" if secondary else "button"}" href="{route("area.html",lang)}#contact" data-book>{label}</a>'

def header(key, lang):
    nav = [('works.html','作品','Work'),('price.html','项目','Services'),('about.html','乐乐老师','Lele'),('posts','专业知识','Journal'),('area.html','到店预约','Visit')]
    links=''.join(f'<a href="{route(k,lang)}"'+(' aria-current="page"' if key==k else '')+f'>{text(z,en,lang)}</a>' for k,z,en in nav)
    other = article_route(key[6:-5],1-lang) if key.startswith('posts/') else route(key,1-lang)
    return f'''<a class="skip" href="#main">{text('跳到主要内容','Skip to content',lang)}</a>
<header class="site-header"><div class="wrap header-inner">
<a class="brand" translate="no" href="{route('home',lang)}" aria-label="{text(BRAND+'首页',BRAND_EN+' home',lang)}"><span><span class="brand-name">描眉画目</span><span class="brand-sub">{text('定制美学 · 私人纹绣工作室','Miaomeihuamu · Bespoke Aesthetics',lang)}</span></span></a>
<nav class="nav" id="primary-nav" aria-label="{text('主导航','Main navigation',lang)}">{links}</nav>
<div class="header-tools"><a class="language-switch" href="{other}" lang="{'zh-CN' if lang else 'en'}" hreflang="{'zh-CN' if lang else 'en'}" aria-label="{text('Switch this page to English','切换此页面为中文',lang)}">{text('EN','中文',lang)}</a><button class="menu-button" aria-expanded="false" aria-controls="primary-nav" type="button">{text('菜单','Menu',lang)}</button></div>
</div></header>'''

def contact(lang):
    return f'''<section class="visit" id="contact"><div class="wrap visit-inner"><div><h2>{text('把想法带来，<br>一起把眉形看清楚。','Bring your ideas.<br>See your design.',lang)}</h2><p class="visit-intro">{text('到店设计免费，约30–45分钟。<br>看过方案，再决定做不做。','A free design consultation, about 30–45 minutes.<br>See the proposed shape before deciding.',lang)}</p><div class="actions">{button(text('微信预约','Contact on WeChat',lang),lang)}<a class="text-link" href="tel:+8619282182068">{text('电话咨询','Call the studio',lang)}</a></div></div><div id="contact-details"><address>{text(BRAND+'<br>上海市浦东新区三林长清路<br>1200弄39号1613室',BRAND_EN+'<br>Room 1613, No. 39, Lane 1200 Changqing Road<br>Sanlin, Pudong, Shanghai',lang)}</address><p class="visit-meta">{text('前滩南侧 · 灵岩南路站2号口往西步行约300米<br>周一至周日 10:00–20:00','South of Qiantan · About 300 m west of Lingyan South Road, Exit 2<br>Daily 10:00–20:00',lang)}</p><div class="visit-links"><a class="text-link" href="{MAP}" target="_blank" rel="noopener noreferrer">{text('打开门店地图','Open the map',lang)}</a><a class="text-link" href="{route('area.html',lang)}">{text('到店路线','Arrival details',lang)}</a></div><p class="visit-small">WeChat: MiaoMeiHuaMu<br>{text('电话：19282182068','Phone: +86 192 8218 2068',lang)}</p></div></div></section>'''

def footer(lang):
    return f'''<footer class="site-footer"><div class="wrap"><div class="footer-top"><div class="footer-brand">{text(BRAND,BRAND_EN,lang)}</div><div class="footer-links"><a href="{route('works.html',lang)}">{text('作品记录','Work records',lang)}</a><a href="{route('price.html',lang)}">{text('全部项目','All services',lang)}</a><a href="{route('posts',lang)}">{text('专业知识','Journal',lang)}</a><a id="reviews" href="{DIANPING}" target="_blank" rel="noopener noreferrer">{text('大众点评门店信息','Current Dianping listing',lang)}</a></div></div><div class="footer-bottom"><span>{text('上海市浦东新区三林镇描眉画目美容店 · 2024年8月开业','Opened August 2024 · Private studio in Pudong, Shanghai',lang)}</span><span>© {text(BRAND,BRAND_EN,lang)}</span></div></div></footer>
<div class="mobile-contact" aria-label="{text('快捷预约','Contact options',lang)}"><a href="tel:+8619282182068">{text('电话咨询','Call',lang)}</a>{button(text('预约免费设计','Free design consultation',lang),lang)}</div>
<dialog class="dialog" id="booking-dialog" aria-labelledby="booking-title"><div class="dialog-content"><button class="close-dialog" type="button" data-close aria-label="{text('关闭预约窗口','Close contact window',lang)}">×</button><h2 id="booking-title">{text('和乐乐老师聊聊','Talk to Lele',lang)}</h2><p>{text('添加微信，说明想了解的项目与方便到店的时间。具体预约时间以老师回复确认为准。','Add the studio on WeChat and mention the service you would like to discuss and a suitable time. Your appointment is confirmed by the studio’s reply.',lang)}</p>{image('assets/wechat-miaomeihuamu.jpg',text('描眉画目微信二维码','Studio WeChat QR code',lang),'qr')}<div class="wechat-line"><strong id="wechat-id">MiaoMeiHuaMu</strong><button type="button" id="copy-wechat">{text('复制微信号','Copy WeChat ID',lang)}</button></div><p class="copy-status" id="copy-wechat-status" role="status" aria-live="polite">{text('也可以长按微信号手动复制。','You can also select and copy the ID manually.',lang)}</p><a class="dialog-phone" href="tel:+8619282182068">{text('电话：19282182068','Phone: +86 192 8218 2068',lang)}</a></div></dialog>
<dialog class="dialog image-dialog" id="image-dialog" aria-label="{text('作品大图','Enlarged work photograph',lang)}"><div class="dialog-content"><button class="close-dialog" type="button" data-close aria-label="{text('关闭大图','Close image',lang)}">×</button><img id="enlarged-image" alt=""><p id="image-caption"></p></div></dialog>
<noscript><style>.menu-button{{display:none}}.nav{{display:flex;position:static;flex-wrap:wrap;flex-direction:row;font-size:13px;padding:0}}.header-inner{{flex-wrap:wrap}}.site-header{{position:static}}</style></noscript>
<script src="/assets/brand-home.js" defer></script>'''

def faqs(lang, indices=None):
    data = [FAQ[i] for i in (indices if indices is not None else range(len(FAQ)))]
    body=''.join(f'<details class="faq"><summary>{e(q[lang])}</summary><p>{e(q[2+lang])}</p></details>' for q in data)
    return f'<section class="wrap section faq-section"><div class="faq-layout"><h2 class="section-title">{text("你可能想问","Questions before a visit",lang)}</h2><div id="faq-list">{body}</div></div></section>', data

def design_section(lang, compact=False):
    items=''.join(f'<div class="approach-item"><h3>{e(d[lang])}</h3><p>{e(d[2+lang])}</p></div>' for d in DESIGN)
    return f'''<section class="section approach" id="design"><div class="wrap approach-inner"><div><h2 class="section-title">{text('眉形设计，<br>先看这些关系。','The details that<br>guide a design.',lang)}</h2><p class="approach-lead">{text('尽量顺应原有骨骼结构，让眉头、眉峰、眉尾与面部比例协调。乐乐偏爱自然柔和，但设计会回应你的喜好，不限于一种眉形。','Work with the existing structure, relating the brow start, arch and tail to facial proportions. Lele favours a natural, soft look personally; each design still responds to your preferences.',lang)}</p><a class="text-link" href="{route('about.html',lang)}">{text('了解乐乐的设计思路','Lele’s approach to design',lang)}</a></div><div class="approach-items">{items}</div></div></section>'''

def layers(lang):
    detail=selection('detail')
    visual=work_figure(detail[0],lang) if detail else ''
    return f'''<section class="wrap section layer-story">{visual}<div><h2 class="section-title">{text('有框架，也有层次。','Structure, with softer layers.',lang)}</h2><p>{text('对于适合采用主线条与绒毛线组合的项目，先建立结构，再讨论内部的疏密与过渡。','Where a combination of structural and fine strokes is appropriate, establish the framework before planning internal density and transitions.',lang)}</p><dl><dt>{text('主线条','Main strokes',lang)}</dt><dd>{text('建立眉形框架、结构与主要毛流。','Establish the framework, structure and primary hair direction.',lang)}</dd><dt>{text('绒毛线','Finer strokes',lang)}</dt><dd>{text('丰富内部层次、密度与柔和过渡。','Add internal layers, density and softer transitions.',lang)}</dd></dl><p>{text('深浅、虚实和方向共同影响视觉上的立体感。不是把眉毛做浓，也不是改变骨骼结构；最终表现因人而异。','Tone, spacing and direction contribute to visual depth. The aim is not simply darker brows, and pigmentation does not change bone structure. Results vary by person.',lang)}</p><a class="text-link" href="{article_route('instrument-vs-dual',lang)}">{text('看单仪器与双仪器的区别','Read about single and dual instruments',lang)}</a></div></section>'''

def cms_text(data, key, lang, breaks=False):
    value = data.get(key + ('_en' if lang else ''), '') or ''
    return e(value).replace('\n', '<br>') if breaks else e(value)

def procedure_label(lang):
    return HOME.get('procedure_alt_en' if lang else 'procedure_alt') or text('本店操作过程记录','A studio procedure record',lang)

def media_upload_date(path):
    revision = [os.environ['CMS_REVISION']] if os.environ.get('CMS_REVISION') else []
    result=subprocess.run(['git','log','--follow','--diff-filter=A','-1','--format=%cI',*revision,'--',path.lstrip('/')],cwd=ROOT,capture_output=True,text=True)
    return result.stdout.strip() if result.returncode == 0 else ''

def work_title(record, lang):
    if lang:
        return record.get('title_en') or next(c[2] for c in CATEGORIES if c[0] == record['_category']) + ' · Work record'
    return record['title']

def work_media(record, lang):
    alt = record.get('alt_en' if lang else 'alt') or work_title(record, lang)
    if record.get('video'):
        poster = record.get('cover') or record.get('image')
        kind = 'video/webm' if record['video'].endswith('.webm') else 'video/mp4'
        return f'<video controls playsinline preload="none" poster="{e(poster)}" aria-label="{e(alt)}"><source src="{e(record["video"])}" type="{kind}"></video>'
    return f'<a href="{e(record["image"])}" data-image>{image(record.get("thumbnail") or record["image"],alt)}</a>'

def work_figure(record, lang, css=''):
    description = record.get('description_en' if lang else 'description') or ''
    if not css and record.get('wide'):
        css = 'work-wide'
    return f'<figure class="{css}">{work_media(record,lang)}<figcaption><h3>{e(work_title(record,lang))}</h3>'+ (f'<p>{e(description)}</p>' if description else '')+'</figcaption></figure>'

def case_pair(lang):
    return '<div class="case-pair">'+''.join(work_figure(r,lang,'case-item') for r in selection('featured'))+'</div>'

def service_list(lang, full=False):
    rows=[]
    for i,s in enumerate(SERVICES if full else SERVICES[:3]):
        rows.append(f'<details class="service" id="{s[0]}"'+(' open' if i==0 else '')+f'><summary><span class="service-name">{e(s[1+lang])}</span></summary><div class="service-content"><p>{e(s[3+lang])}</p></div></details>')
    if not full:
        rows.append('<div class="other-projects"><h3>'+text('其他实际项目','Other available services',lang)+'</h3><div class="project-links">'+''.join(f'<a href="{route("price.html",lang)}#{s[0]}">{e(s[1+lang])}</a>' for s in SERVICES[3:])+'</div></div>')
    rows.append(f'<p class="service-policy">{text("所有项目一年内免费补色。具体价格以","All services include free touch-ups within one year. For prices, see the ",lang)}<a href="{DIANPING}" target="_blank" rel="noopener noreferrer">{text("大众点评当期门店信息","current Dianping listing",lang)}</a>{text("为准。",".",lang)}</p>')
    return ''.join(rows)

def home(lang):
    body=f'''<section class="wrap hero" aria-labelledby="hero-title"><figure class="hero-visual">{image(HOME['hero_image'],HOME.get('hero_alt_en' if lang else 'hero_alt') or HOME['hero_alt'],'hero-image',True,'hero-image') if HOME.get('hero_image') else ''}<figcaption class="hero-caption"><span id="hero-badge">{cms_text(HOME,'hero_badge',lang)}</span></figcaption></figure><div class="hero-copy"><h1 id="hero-title">{cms_text(HOME,'hero_title',lang,True)}</h1><p class="hero-intro">{cms_text(HOME,'hero_intro',lang,True)}</p><div class="actions">{button(text('预约免费设计','Book a free design consultation',lang),lang)}<a class="text-link" href="#works">{text('看真实作品','Explore the work',lang)}</a></div><p class="hero-note">{cms_text(HOME,'hero_note',lang,True)}</p></div></section>
<div class="wrap studio-line">{text('乐乐老师本人一对一设计操作 · 所有项目一年内免费补色','Designed and performed personally by Lele · Free touch-ups within one year for all services',lang)}</div>
<section class="wrap section" id="works"><div class="section-heading"><div><h2>{cms_text(HOME,'works_title',lang,True)}</h2><p>{cms_text(HOME,'works_intro',lang,True)}</p></div><a class="text-link" href="{route('works.html',lang)}">{text('查看作品与设计记录','Explore work and design notes',lang)}</a></div><div id="works-grid">{case_pair(lang)}</div></section>
{design_section(lang)}{layers(lang)}
<section class="wrap section" id="services"><div class="services-layout"><div><h2 class="section-title">{text('设计在前，<br>项目随之选择。','The design comes first.<br>The method follows.',lang)}</h2><p class="service-note">{text('以仪器野生眉私人定制为主打。具体做法结合基础、底色、肤质和希望呈现的风格，不按固定眉形或项目档位套用。','Instrument hair-stroke brows are the main service. Existing brows, old pigment, skin and your preferences guide the method, rather than a fixed shape or a service tier.',lang)}</p><a class="text-link" href="{route('price.html',lang)}">{text('完整项目与护理说明','All services and care information',lang)}</a></div><div>{service_list(lang)}</div></div></section>
<section class="wrap section artist" id="lele"><div class="artist-inner"><figure class="artist-image" id="studio">{image(STUDIO['image'],STUDIO.get('image_alt_en' if lang else 'image_alt') or STUDIO['image_alt']) if STUDIO.get('image') else ''}<figcaption>{text('工作室的一角','A corner of the studio',lang)}</figcaption></figure><div class="artist-copy"><h2>{text('乐乐老师','Meet Lele',lang)}</h2><p>{cms_text(STUDIO,'home_intro',lang,True)}</p><p>{cms_text(STUDIO,'home_history',lang,True)}</p><a class="text-link" href="{route('about.html',lang)}">{text('认识乐乐与工作室','About Lele and the studio',lang)}</a></div></div></section>
<section class="wrap section journal" id="journal"><div class="section-heading"><h2>{text('先了解，再决定。','Understand the work<br>before deciding.',lang)}</h2><a class="text-link" href="{route('posts',lang)}">{text('浏览专业知识','Browse the journal',lang)}</a></div><div class="journal-editorial"><figure><video controls playsinline preload="none" poster="{e(HOME.get('procedure_cover') or '')}" aria-label="{e(procedure_label(lang))}"><source src="{e(HOME.get('procedure_video') or '')}" type="{'video/webm' if (HOME.get('procedure_video') or '').endswith('.webm') else 'video/mp4'}"></video><figcaption>{e(procedure_label(lang))}</figcaption></figure><div class="reading-list">'''
    for slug in ['wild-brow-9-steps','instrument-vs-dual','first-month']:
        a=next(a for a in ARTICLES if a['slug']==slug)
        body+=f'<a href="{article_route(slug,lang)}"><h3>{e(a["title"][lang])}</h3><p>{e(a["intro"][lang])}</p><span aria-hidden="true">↗</span></a>'
    body+='</div></div></section>'
    faq,data=faqs(lang,[0,1,2,3,5])
    if not HOME.get('hero_image'):
        body=re.sub(r'<figure class="hero-visual">.*?</figure>', '', body, count=1, flags=re.S)
        body=body.replace('class="wrap hero"', 'class="wrap hero hero-text-only"')
    if not HOME.get('procedure_video'):
        body=re.sub(r'(<div class="journal-editorial">)<figure>.*?</figure>', r'\1', body, count=1, flags=re.S)
    return body+faq, data


def gallery_records(category,lang):
    records=work_records(category)
    return records, ''.join(work_figure(record,lang) for record in records)


def works(lang):
    intro=cms_text(WORKS_PAGE,'intro',lang)
    body=page_intro(cms_text(WORKS_PAGE,'title',lang),intro,lang)
    body+=f'<section class="wrap section selected-works">{case_pair(lang)}</section>'
    details=selection('detail')
    if details:
        body+='<section class="wrap section closeup-pair"><div><h2 class="section-title">'+text('近看，线条怎样衔接。','A closer look at the transitions.',lang)+'</h2></div>'+''.join(work_figure(r,lang) for r in details)+'</section>'
    body+=f'<section class="wrap section archive" id="archive"><h2 class="section-title">{text("按项目浏览全部记录","Browse all work records",lang)}</h2><p class="archive-note">{text("展开项目查看照片，点击图片可放大。未标注恢复时间的记录，不用于判断长期留色。","Open a category and select an image to enlarge it. Images without a documented healing stage do not establish long-term pigment retention.",lang)}</p>'
    for cat,zh,en in CATEGORIES:
        records,markup=gallery_records(cat,lang)
        body+=f'<details class="archive-group" id="{cat}" data-gallery="{cat}"'+(' hidden' if not records else '')+f'><summary><span>{text(zh,en,lang)}</span><span class="gallery-count">{len(records)} {text("组记录","records",lang)}</span></summary><div class="archive-grid">{markup}</div></details>'
    return body+'</section>',[]

def page_intro(title,intro,lang):
    return f'<section class="wrap page-intro"><h1>{title}</h1><p>{intro}</p></section>'

def services(lang):
    body=page_intro(text('先找到适合的设计，<br>再选择做法。','Start with the design.<br>Then choose the method.',lang),text('主打仪器野生眉私人定制，也保留工作室实际提供的其他项目。所有项目先评估适用情况，价格以大众点评当期门店信息为准。','Instrument hair-stroke brows are the main service, alongside the other treatments offered by the studio. Suitability is assessed first; check the current Dianping listing for prices.',lang),lang)
    body+=f'<section class="wrap section service-page"><div><h2 class="section-title">{text("服务项目","Available services",lang)}</h2><p>{text("所有项目一年内免费补色。到店设计免费，约30–45分钟；看过眉形再决定，不做也不收费。","All services include free touch-ups within one year. The design consultation is free and takes about 30–45 minutes, even if you decide not to proceed.",lang)}</p></div><div>{service_list(lang,True)}</div></section>'
    body+=f'<section class="wrap section care-note"><h2>{text("恢复与留色：时间是参考，不是保证。","Healing and retention: estimates, not guarantees.",lang)}</h2><p>{text("手工野生眉留色通常参考约1年，单仪器与双仪器通常参考约2–3年。手工前一周颜色可能偏深；扩唇与改乌唇可能出现结痂。改乌唇不预设统一恢复天数。","Retention is commonly discussed as around one year for manual brows and two to three for instrument brows. Manual work may appear darker during the first week. Lip-contour and dark-lip work may involve surface flaking; no fixed recovery period is assigned to dark-lip correction.",lang)}</p><p>{text("个人肤质、原有底色、操作和护理都会影响表现。洗脸、化妆、游泳或运动的安排应按本次项目与实际恢复情况确认。","Skin, existing pigment, the procedure and aftercare can affect the outcome. Confirm washing, makeup, swimming and exercise arrangements for the specific service and actual healing.",lang)}</p><a class="text-link" href="{route('wild-brow.html',lang)}">{text("比较三种野生眉做法","Compare the three brow methods",lang)}</a></section>'
    faq,data=faqs(lang,[1,2,3,4]);return body+faq,data

def about(lang):
    body=page_intro(cms_text(STUDIO,'title',lang,True),cms_text(STUDIO,'intro',lang),lang)
    body+=f'<section class="wrap section artist"><div class="artist-inner"><figure class="artist-image">{image(STUDIO['image'],STUDIO.get('image_alt_en' if lang else 'image_alt') or STUDIO['image_alt']) if STUDIO.get('image') else ''}<figcaption>{text("真实工作室环境","Inside the studio",lang)}</figcaption></figure><div class="artist-copy"><h2>{text("从从业经验，到个人工作室。","From professional experience<br>to a private studio.",lang)}</h2><p>{cms_text(STUDIO,'history',lang)}</p><p>{cms_text(STUDIO,'current',lang)}</p></div></div></section>'
    body+=design_section(lang)+layers(lang)
    body+=f'<section class="wrap section personal-note"><h2>{text("你的风格，也在设计里。","Your preferences belong in the design.",lang)}</h2><p>{text("喜欢柔和、利落，或希望眉形更有存在感，都可以说清楚。设计尽量顺应原有骨骼结构，通过眉头、眉峰、眉尾与整体轮廓的调整，追求视觉上的面部流畅度、比例协调和立体感。","Whether you prefer softness, definition or a stronger brow presence, say so. The design works with existing bone structure, adjusting the start, arch, tail and contour to seek visual flow, balanced proportions and depth.",lang)}</p><p>{text("这些是设计目标，不是必然发生的效果，也不是改变实际骨骼结构。","These are design aims, not guaranteed outcomes or changes to actual bone structure.",lang)}</p></section>'
    return body,[]

def area(lang):
    body=page_intro(text('来工作室，<br>先看设计，再决定。','Visit the studio.<br>See the design before deciding.',lang),text('到店设计免费，约30–45分钟。一对一接待，建议先联系确认时间。','The design consultation is free and takes about 30–45 minutes. Visits are one-to-one; contact the studio to confirm a time.',lang),lang)
    steps=[('联系确认时间','Arrange a time','微信MiaoMeiHuaMu，或致电19282182068。可以先说希望了解的项目和方便到店的时间。','Use WeChat MiaoMeiHuaMu or call +86 192 8218 2068. Mention the service you would like to discuss and when you can visit.'),('观察与设计','Discuss and design','结合五官、骨骼轮廓、原生眉与喜好，先把眉形画出来给你看。可带日常照片或喜欢的眉形作沟通参考。','Discuss facial features, contours, existing brows and preferences, then see a proposed shape. Everyday photographs or brow references can help explain what you like.'),('确认是否操作','Decide whether to proceed','你觉得合适再决定，不做也不收费。操作前说清项目、护理要求和实际安排。','Decide after seeing the design. There is no charge if you do not proceed. The service, aftercare and practical arrangements are discussed beforehand.'),('护理与复看','Aftercare and review','按本次项目说明护理，结合恢复状态复看。所有项目一年内免费补色。','Follow the aftercare for your service and arrange review according to healing. All services include free touch-ups within one year.')]
    body+='<section class="wrap section visit-process"><div>'+''.join(f'<div><h2>{s[lang]}</h2><p>{s[2+lang]}</p></div>' for s in steps)+f'</div><figure class="studio-photo">{image(STUDIO['image'],STUDIO.get('image_alt_en' if lang else 'image_alt') or STUDIO['image_alt']) if STUDIO.get('image') else ''}<figcaption>{text("工作室真实环境","The real studio interior",lang)}</figcaption></figure></section>'
    body+=f'<section class="wrap section arrival"><h2 class="section-title">{text("怎么到店","Getting here",lang)}</h2><p>{text("上海市浦东新区三林长清路1200弄39号1613室，前滩南侧。地铁6号线灵岩南路站2号口往西步行约300米。到楼后如不确定入口，可联系工作室确认。","Room 1613, No. 39, Lane 1200 Changqing Road, Sanlin, Pudong, Shanghai, south of Qiantan. Walk about 300 metres west from Exit 2 of Lingyan South Road station on Metro Line 6. Contact the studio if you need help finding the entrance.",lang)}</p><p>{text("周一至周日10:00–20:00。门店品牌名与营业执照登记名可能不同，地图或点评长名称指向同一工作室。","Open daily 10:00–20:00. The trading name and registered business name can differ; the longer category-based name on maps or Dianping refers to the same studio.",lang)}</p></section>'
    faq,data=faqs(lang,[1,3,5]);return body+faq,data

def methods(lang):
    body=page_intro(text('三种做法，<br>从同一个人出发。','Three methods.<br>One individual starting point.',lang),text('工具与线条组织不同，设计依据却始终是五官、原生眉和顾客偏好。','Tools and stroke arrangements differ. The design still begins with facial features, existing brows and individual preference.',lang),lang)
    body+=f'<section class="wrap section methods-list">{service_list(lang)}</section>'+layers(lang)
    faq,data=faqs(lang,[0,3,4]);return body+faq,data

def journal(lang):
    body=page_intro(text('关于眉形，<br>把问题说具体。','Thoughtful questions.<br>Practical explanations.',lang),text('设计、毛流、项目选择与日常护理。一篇解释一个问题，不用项目名称代替对自己的了解。','Design, hair direction, choosing a service and everyday care. One topic at a time, grounded in the individual rather than a service label.',lang),lang)
    body+='<section class="wrap section article-index">'
    ordered=sorted(ARTICLES,key=lambda a:0 if a['slug']=='wild-brow-9-steps' else 1)
    for a in ordered:
        body+=f'<a href="{article_route(a["slug"],lang)}"><h2>{e(a["title"][lang])}</h2><p>{e(a["intro"][lang])}</p><span aria-hidden="true">↗</span></a>'
    return body+'</section>',[]

def article_body(a,lang):
    body=f'<article class="wrap article-page"><header class="article-heading"><a class="text-link" href="{route("posts",lang)}">{text("全部专业知识","All journal articles",lang)}</a><h1>{e(a["title"][lang])}</h1><p class="article-lead">{e(a["intro"][lang])}</p></header><div class="article-body">'
    for i,s in enumerate(a['sections'],1):
        title=(str(i)+'. ' if a['slug']=='wild-brow-9-steps' else '')+s[lang]
        body+=f'<section id="section-{i}"><h2>{e(title)}</h2><p>{e(s[2+lang])}</p>'
        if a['section_images'][i-1]:
            body+=f'<figure>{image(a["section_images"][i-1],title)}<figcaption>{e(title)}</figcaption></figure>'
        body+='</section>'
    body+=f'<nav class="article-related" aria-label="{text("相关阅读","Related reading",lang)}"><a href="{route("works.html",lang)}">{text("看真实作品","See the work",lang)}</a><a href="{route("wild-brow.html",lang)}">{text("比较野生眉做法","Compare brow methods",lang)}</a><a href="{route("area.html",lang)}">{text("到店设计与预约","Consultation and arrival",lang)}</a></nav></div></article>'
    return body,[]

GENERATED=[]

def update_machine_readable():
    def save(path,data):
        (ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary=json.loads((ROOT/'ai/summary.json').read_text(encoding='utf-8'))
    summary['description']=BUSINESS['description']
    summary['design_principles']={'personal_preference':'乐乐老师个人审美偏自然柔和、原生态，不限制顾客定制其他眉形风格。','observations':[d[0]+'：'+d[2] for d in DESIGN],'main_strokes':'建立眉形框架、结构与主要毛流。','fine_strokes':'在适合组合的项目中丰富内部层次、密度与柔和过渡。','limits':'设计追求视觉协调，不改变实际骨骼结构，不保证统一效果。'}
    care='恢复与留色因项目、个人肤质、原有底色、操作和护理而异。洗脸、化妆、游泳或运动需按本次项目及实际恢复情况确认，不承诺统一无痛或即刻恢复。'
    summary['policies']['waterContact']=care
    summary['policies']['touchColor']='所有项目一年内免费补色'
    summary['policies']['freeDesign']='到店设计免费，约30–45分钟，不做也不收费。'
    summary['updated']=DATE
    save('ai/summary.json',summary)
    services=json.loads((ROOT/'ai/service.json').read_text(encoding='utf-8'))
    services['services']=[{'name':s[1],'english_name':s[2],'description':s[3],'touch_up':'一年内免费补色'} for s in SERVICES]
    for row in services['services']:
        if row['name']=='手工野生眉': row.update(duration='留色通常参考约1年，实际因人而异',recovery_period='约7天为经验参考，实际因人而异')
        if row['name'] in ('画派单仪器野生眉','画派双仪器初绒野生眉'): row['duration']='留色通常参考约2–3年，实际因人而异'
        if row['name']=='扩唇 / 唇形调整': row.update(recovery='可能有结痂期',recovery_period='约3天为经验参考，实际因人而异')
        if row['name']=='改乌唇': row['recovery']='可能有结痂期；恢复时间按评估说明'
    services['booking']['mode']='预约制，乐乐老师本人一对一设计操作，时间以联系确认为准。'
    services['aftercare']=care;services['updated']=DATE
    save('ai/service.json',services)
    faq=json.loads((ROOT/'ai/faq.json').read_text(encoding='utf-8'))
    faq['faqs']=faq['faqs'][:2]+[{'q':q[0],'a':q[2]} for q in FAQ]
    faq['updated']=DATE;save('ai/faq.json',faq)
    save('ai/en.json',{'name':BRAND,'alternateName':BRAND_EN,'url':BASE+'/','page':BASE+'/en/','inLanguage':'en','description':'A private studio centred on personal aesthetic judgement and individual brow design. Instrument hair-stroke brows are the main service; designs respond to the individual rather than one fixed style.','design_considerations':[d[1]+': '+d[3] for d in DESIGN],'services':[{'name':s[2],'original_name':s[1],'description':s[4]} for s in SERVICES],'faqs':[{'q':q[1],'a':q[3]} for q in FAQ],'updated':DATE})
    llms=f'''# {BRAND}

以个人审美和专业眉形设计为核心的私人定制纹绣工作室，主打仪器野生眉。
乐乐老师个人偏爱自然柔和、原生态；可以根据顾客要求定制不同风格，不局限于温柔眉。

## 门店事实
- 主理人：乐乐老师，2016年进入纹绣行业；工作室2024年8月开业。
- 地址：上海市浦东新区三林长清路1200弄39号1613室，前滩南侧。
- 地铁：6号线灵岩南路站2号口往西步行约300米。
- 营业时间：周一至周日10:00–20:00；本人一对一设计操作，建议提前联系确认。
- 电话：19282182068；微信：MiaoMeiHuaMu。
- 到店设计免费，约30–45分钟；不做也不收费。
- 所有项目一年内免费补色。
- 不主动展示具体价格；以大众点评当期门店信息为准：{DIANPING}

## 设计依据
'''+ '\n'.join('- '+d[0]+'：'+d[2] for d in DESIGN)+'''

主线条建立框架、结构与主要毛流；适合组合的项目中，绒毛线丰富内部层次、密度与柔和过渡。
这些调整追求视觉协调，不改变实际骨骼结构，不保证每个人呈现同样效果。

## 实际项目
'''+ '\n'.join('- '+s[1]+'：'+s[3] for s in SERVICES)+f'''

## 恢复与留色
{care}
手工留色约1年、仪器约2–3年，仅为经验参考，不是保证期限。改乌唇不预设统一恢复天数。

## 中文入口
'''+ '\n'.join(f'- [{label}]({BASE}{route(key)})' for key,label in [('home','首页'),('works.html','真实作品'),('about.html','乐乐老师与设计理念'),('price.html','服务项目'),('wild-brow.html','野生眉做法'),('posts','专业知识'),('area.html','预约与到店')])+f'''

## English pages
English-language pages explain the same studio and services.
'''+ '\n'.join(f'- [{label}]({BASE}{route(key,1)})' for key,label in [('home','Home'),('works.html','Work'),('about.html','Lele'),('price.html','Services'),('posts','Journal'),('area.html','Visit'),('guide','Choosing a brow studio')])+f'''

## Structured information
- {BASE}/ai/summary.json
- {BASE}/ai/service.json
- {BASE}/ai/faq.json
- {BASE}/ai/en.json
- {BASE}/sitemap.xml

Updated: {DATE}
'''
    (ROOT/'llms.txt').write_text(llms,encoding='utf-8')
    ai_notes=ROOT/'.well-known/ai.txt'
    notes=ai_notes.read_text(encoding='utf-8')
    notes=re.sub(r'# 更新：.*', '# 更新：'+DATE,notes)
    notes=re.sub(r'# 碰水：.*','# 护理：按项目与实际恢复情况确认，不承诺统一无痛或即刻恢复。',notes)
    if 'English:' not in notes: notes+='\nEnglish: '+BASE+'/en/\nEnglish-Summary: '+BASE+'/ai/en.json\n'
    ai_notes.write_text(notes,encoding='utf-8')
    feed=ROOT/'feed.xml'
    tree=ET.parse(feed)
    for item in tree.getroot().iter('item'):
        link=item.findtext('link','')
        for a in ARTICLES:
            if link==BASE+article_route(a['slug'],0):
                for tag,value in [('title',a['title'][0]),('description',a['intro'][0])]:
                    node=item.find(tag)
                    if node is None: node=ET.SubElement(item,tag)
                    node.text=value
    ET.indent(tree,space='  ');tree.write(feed,encoding='utf-8',xml_declaration=True)

def render(key,path,lang,title,description,body,faq_data,article_data=None):
    if not STUDIO.get('image'):
        body=re.sub(r'<figure class="(?:artist-image|studio-photo)"[^>]*>.*?</figure>', '', body, flags=re.S)
    canonical=BASE+path
    other=article_route(article_data['slug'],1-lang) if article_data else route(key,1-lang)
    zh_url=BASE+(other if lang else path); en_url=BASE+(path if lang else other)
    source_path=disk(path).relative_to(ROOT).as_posix()
    # Use the corresponding original page only for metadata, never for its old UI.
    old=ORIGINALS.get(source_path,{})
    schemas=[]
    if key=='home':
        business=copy.deepcopy(BUSINESS)
        if lang: business['@type']='BeautySalon'
        schemas.extend([business,PERSON,{'@context':'https://schema.org','@type':'WebSite','@id':BASE+'/#website','url':BASE+'/','name':BRAND,'inLanguage':['zh-CN','en']}])
        if HOME.get('procedure_video'):
            video_schema=copy.deepcopy(VIDEO)
            video_schema.update(contentUrl=BASE+HOME['procedure_video'],thumbnailUrl=BASE+HOME['procedure_cover'],name=procedure_label(lang))
            video_schema.pop('embedUrl',None)
            if video_schema['contentUrl'] != VIDEO.get('contentUrl'):
                video_schema['description']=procedure_label(lang)
                video_schema.pop('duration',None)
                uploaded=media_upload_date(HOME['procedure_video'])
                if uploaded:
                    video_schema['uploadDate']=uploaded
                else:
                    video_schema.pop('uploadDate',None)
            schemas.append(video_schema)
    kind='Article' if article_data else ('CollectionPage' if key in ('works.html','posts') else 'AboutPage' if key=='about.html' else 'WebPage')
    previous=next((s for s in old.get('schemas',[]) if s.get('@type')==kind),{})
    page={**previous,'@context':'https://schema.org','@type':kind,'@id':canonical+'#webpage','url':canonical,'name':title,'description':description,'inLanguage':'en' if lang else 'zh-CN','about':{'@id':BASE+'/#business'}}
    page['isPartOf']={'@id':BASE+'/#website'}
    if key=='about.html': page['mainEntity']={'@id':BASE+'/#business'}
    if key=='works.html':
        records=[]
        for category,zh,en in CATEGORIES:
            data,_=gallery_records(category,lang)
            for i,record in enumerate(data,1):
                record_title=record.get('title','作品记录') if not lang else record.get('title_en',f'{en} · Work record {i}')
                item={'@type':'VideoObject' if record.get('video') else 'ImageObject','name':record_title,'contentUrl':BASE+(record.get('video') or record['image'])}
                record_description=record.get('description','') if not lang else record.get('description_en','')
                if record.get('video'):item['thumbnailUrl']=BASE+(record.get('cover') or record['image'])
                if record_description:item['description']=record_description
                records.append({'@type':'ListItem','position':len(records)+1,'item':item})
        page['mainEntity']={'@type':'ItemList','numberOfItems':len(records),'itemListElement':records}
    if article_data:
        page.update(headline=title,dateModified=DATE,author={'@type':'Person','name':'乐乐老师','url':BASE+'/about.html'})
        page.pop('articleBody',None)
        page['mainEntityOfPage']=canonical
    schemas.append(page)
    if article_data and article_data['slug']=='wild-brow-9-steps':
        schemas.append({'@context':'https://schema.org','@type':'HowTo','name':title,'description':description,'inLanguage':'en' if lang else 'zh-CN','image':BASE+article_data['section_images'][0],'step':[{'@type':'HowToStep','position':i,'name':s[lang],'text':s[2+lang],'url':canonical+f'#section-{i}','image':BASE+article_data['section_images'][i-1]} for i,s in enumerate(article_data['sections'],1)]})
    crumbs=[{'@type':'ListItem','position':1,'name':text('首页','Home',lang),'item':BASE+route('home',lang)}]
    if key!='home': crumbs.append({'@type':'ListItem','position':2,'name':title,'item':canonical})
    schemas.append({'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':crumbs})
    if faq_data:
        schemas.append({'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q[lang],'acceptedAnswer':{'@type':'Answer','text':q[2+lang]}} for q in faq_data]})
    structured='\n'.join('<script type="application/ld+json">'+json.dumps(s,ensure_ascii=False,indent=2).replace('</',r'<\/')+'</script>' for s in schemas)
    existing_ids=set(re.findall(r'\bid="([^"]+)"',header(key,lang)+body+contact(lang)+footer(lang)))|{'main'}
    legacy=''.join(f'<span class="legacy-anchor" id="{e(anchor)}" aria-hidden="true"></span>' for anchor in old.get('ids',[]) if anchor not in existing_ids)
    result=f'''<!doctype html>
<html lang="{'en' if lang else 'zh-CN'}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%23692f43'/%3E%3Cpath d='M16 33c8-12 24-12 32 0-8 11-24 11-32 0Zm7 0c5 5 13 5 18 0-5-6-13-6-18 0Z' fill='%23fffdfc'/%3E%3C/svg%3E">
{'<meta name="google" content="notranslate">' if lang else ''}
<title>{e(title)} | {e(text(BRAND,BRAND_EN,lang))}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="zh-CN" href="{zh_url}"><link rel="alternate" hreflang="en" href="{en_url}"><link rel="alternate" hreflang="x-default" href="{zh_url}">
<link rel="alternate" type="application/rss+xml" title="{BRAND}" href="{BASE}/feed.xml">
<meta property="og:type" content="{'article' if article_data else 'website'}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{canonical}">{('<meta property="og:image" content="'+BASE+e(HOME['hero_image'])+'">') if HOME.get('hero_image') else ''}
<meta name="theme-color" content="#f5f3ed"><meta name="color-scheme" content="light">
<link rel="stylesheet" href="/assets/brand-home.css"><link rel="stylesheet" href="/assets/brand-stage2.css">
{('<link rel="preload" as="image" href="'+e(HOME['hero_image'])+'">') if key=='home' and HOME.get('hero_image') else ''}
{structured}
</head><body class="{'home-page' if key=='home' else 'inner-page'}">
{header(key,lang)}
<main id="main">{legacy}{body}{contact(lang)}</main>
{footer(lang)}
</body></html>
'''
    target=disk(path);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(result,encoding='utf-8',newline='\n')
    GENERATED.append(path)

def build():
    validate()
    pages=[('home',home,['仪器野生眉与私人眉形设计','Individual brow design and hair-stroke brows']),('works.html',works,['真实作品与设计记录','Real work and design notes']),('price.html',services,['服务项目与护理说明','Services and aftercare']),('about.html',about,['乐乐老师与设计理念','Lele and her design approach']),('area.html',area,['免费到店设计与预约','Free design consultation and arrival']),('wild-brow.html',methods,['手工、单仪器与双仪器野生眉','Manual, single- and dual-instrument brows']),('posts',journal,['眉形设计与纹绣专业知识','Brow design and pigmentation journal'])]
    for lang in (0,1):
        for key,fn,titles in pages:
            body,data=fn(lang)
            desc=text('描眉画目私人定制纹绣工作室，结合五官、原生眉和个人偏好设计。主打仪器野生眉，免费设计约30–45分钟，所有项目一年内免费补色。','A private studio for individual brow design in Pudong, Shanghai. A free 30–45 minute design consultation and free touch-ups within one year for all services.',lang)
            render(key,route(key,lang),lang,titles[lang],desc,body,data)
        for a in ARTICLES:
            body,data=article_body(a,lang)
            key='guide' if a['slug']=='eyebrow-tattoo-shanghai-guide' else 'posts/'+a['slug']+'.html'
            render(key,article_route(a['slug'],lang),lang,a['title'][lang],a['intro'][lang],body,data,a)
    ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
    sitemap=ROOT/'sitemap.xml';tree=ET.parse(sitemap);root=tree.getroot()
    known={n.find('{'+ns+'}loc').text:n for n in root.findall('{'+ns+'}url')}
    for path in GENERATED:
        url=BASE+path
        node=known.get(url)
        if node is None:
            node=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(node,'{'+ns+'}loc').text=url
        modified=node.find('{'+ns+'}lastmod')
        if modified is None:modified=ET.SubElement(node,'{'+ns+'}lastmod')
        modified.text=DATE
    ET.indent(tree,space='  ');tree.write(sitemap,encoding='utf-8',xml_declaration=True)
    (ROOT/'content/brand/routes.json').write_text(json.dumps(GENERATED,indent=2)+'\n',encoding='utf-8')
    update_machine_readable()
    (ROOT/'admin/release.json').write_text(json.dumps(release_metadata(),indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(GENERATED)} static pages; existing sitemap URLs retained.')

if __name__=='__main__':
    build()
