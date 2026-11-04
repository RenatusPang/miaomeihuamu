"""Read and validate owner-managed JSON before generating a public site.

Media paths are local assets, never executable URLs. Hidden records are excluded
from every presentation, including curated selections and structured data.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.webm'}
CATEGORIES = [
    ('women-brow', '女士眉形', 'Women’s brows'),
    ('men-brow', '男士眉形', 'Men’s brows'),
    ('lip-extension', '唇形调整', 'Lip-contour refinement'),
    ('hairline', '发际线', 'Hairline pigmentation'),
    ('philtrum', '人中窝', 'Philtrum shading'),
    ('eyeliner', '美瞳线', 'Lash-line enhancement'),
    ('dark-lip-correction', '改乌唇', 'Dark-lip colour correction'),
]


def load(name, kind=dict):
    value = json.loads((ROOT / 'content' / name).read_text(encoding='utf-8'))
    if not isinstance(value, kind):
        raise ValueError(f'content/{name}: expected {kind.__name__}')
    return value


def local_media(value, video=False, required=False):
    if not value:
        if required:
            raise ValueError('请填写图片或视频路径 / A media path is required')
        return ''
    if not isinstance(value, str) or not value.startswith('/assets/') or any(c in value for c in ('\\', '?', '#', '%', '\x00')):
        raise ValueError(f'只允许本地 assets 媒体路径 / Invalid media path: {value!r}')
    target = (ROOT / value.lstrip('/')).resolve()
    if not target.is_relative_to((ROOT / 'assets').resolve()) or '..' in Path(value).parts:
        raise ValueError(f'媒体路径越界 / Invalid media path: {value!r}')
    extensions = VIDEO_EXTENSIONS if video else IMAGE_EXTENSIONS
    if target.suffix.lower() not in extensions or not target.is_file():
        raise ValueError(f'媒体文件不存在或格式不支持 / Missing or unsupported media: {value}')
    # Kept below the common web upload boundary; do not add Git LFS for Pages.
    limit = (24 if video else 20) * 1024 * 1024
    if target.stat().st_size > limit:
        raise ValueError(f'媒体过大，请先压缩 / Media exceeds {limit // 1024 // 1024} MiB: {value}')
    return value


def number(value, fallback):
    if value is None or value == '':
        return fallback
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('排序值必须是数字 / Sort order must be numeric')
    return value


def work_records(category, public_only=True):
    rows = load(f'works/{category}.json', list)
    records = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get('published'), bool):
            raise ValueError(f'{category}[{index}]: published must be a boolean')
        if public_only and not row['published']:
            continue
        record = dict(row)
        for key in ('image', 'thumbnail', 'cover'):
            record[key] = local_media(row.get(key))
        record['video'] = local_media(row.get('video'), video=True)
        if not (record['image'] or record['video']):
            if row['published']:
                raise ValueError(f'{category}[{index}]: 展示作品须有图片或视频')
            continue
        if not isinstance(row.get('title'), str) or not row['title'].strip():
            raise ValueError(f'{category}[{index}]: 请填写作品标题')
        if not isinstance(row.get('alt'), str) or not row['alt'].strip():
            raise ValueError(f'{category}[{index}]: 请填写替代文字')
        if record['video'] and not (record['cover'] or record['image']):
            raise ValueError(f'{category}[{index}]: 视频须设置封面')
        # The CMS array's drag order is the archive's display order.
        record['_order'] = (index + 1) * 10
        record['_featured_order'] = number(row.get('featured_order'), record['_order'])
        record['_category'] = category
        records.append(record)
    return sorted(records, key=lambda r: r['_order'])


def all_works():
    return [r for category, _, _ in CATEGORIES for r in work_records(category)]


def selection(flag):
    return sorted((r for r in all_works() if r.get(flag) is True),
                  key=lambda r: r['_featured_order'] if flag == 'featured' else r['_order'])


def validate():
    home = load('home.json')
    local_media(home.get('hero_image'))
    if home.get('hero_image') and not home.get('hero_alt', '').strip():
        raise ValueError('首页图片须填写替代文字')
    local_media(home.get('procedure_video'), video=True)
    local_media(home.get('procedure_cover'), required=bool(home.get('procedure_video')))
    studio = load('studio.json')
    local_media(studio.get('image'))
    if studio.get('image') and not studio.get('image_alt', '').strip():
        raise ValueError('工作室图片须填写替代文字')
    for suffix in ('', '_en'):
        for key in ('design_intro','layers_intro','main_strokes','fine_strokes','layers_result'):
            if not isinstance(home.get(key+suffix),str) or not home[key+suffix].strip():
                raise ValueError(f'{key+suffix}: 请保留首页设计理念文字')
        for part,minimum in (('bone',3),('strokes',4),('style',3)):
            title=studio.get('philosophy_'+part+'_title'+suffix)
            body=studio.get('philosophy_'+part+'_body'+suffix)
            if not isinstance(title,str) or not title.strip() or not isinstance(body,str):
                raise ValueError(f'{part+suffix}: 请保留正式设计理念标题与正文')
            if len([p for p in re.split(r'\n\s*\n',body) if p.strip()]) < minimum:
                raise ValueError(f'{part+suffix}: 段落之间留空行，保留至少{minimum}段正式理念')
        if not isinstance(studio.get('philosophy_summary'+suffix),str) or not studio['philosophy_summary'+suffix].strip():
            raise ValueError('请保留中英文正式设计理念总述')
    for category, _, _ in CATEGORIES:
        work_records(category)
    services = load('services.json', list)
    expected = {'single', 'dual', 'hand', 'silk', 'velvet', 'eyeline', 'lip', 'dark-lip', 'hairline', 'philtrum'}
    if {r.get('id') for r in services} != expected or len(services) != len(expected):
        raise ValueError('请保留原有十类服务及网址标识；项目变更须先核对门店实际服务')
    if len(load('design.json', list)) != 6 or len(load('faq.json', list)) != 6:
        raise ValueError('请保留六项设计依据和六条常见问题，可修改对应中英文文字')
    for path in (ROOT / 'content/articles').glob('*.json'):
        article = load('articles/' + path.name)
        slug = article.get('slug')
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or slug != path.stem:
            raise ValueError(f'{path.name}: 文章网址标识必须与文件名一致，不能改为路径')
        if not isinstance(article.get('sections'), list) or not article['sections']:
            raise ValueError(f'{path.name}: 请保留文章正文段落')
        for section in article['sections']:
            local_media(section.get('image'), required=slug == 'wild-brow-9-steps')
    for data in (home, studio, load('works-page.json')):
        for key, value in data.items():
            if not isinstance(value, (str, type(None))):
                raise ValueError(f'{key}: 文字字段只能填写文字')
    return {'public_works': len(all_works()), 'featured': len(selection('featured'))}
