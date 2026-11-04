"""Exercise CMS changes against the real generator in a disposable copy.

These tests never touch the active work records or a remote repository.
Run: python tools/test_cms.py
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ContentFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='miaomeihuamu-cms-')
        cls.root = Path(cls.temporary.name).resolve()
        if cls.root.parent != Path(tempfile.gettempdir()).resolve():
            raise RuntimeError('Unexpected test directory')
        shutil.copytree(ROOT, cls.root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', '_site', '__pycache__', '.github'))
        cls.path = cls.root / 'content/works/women-brow.json'
        cls.records = json.loads(cls.path.read_text(encoding='utf-8'))
        cls.home_path = cls.root / 'content/home.json'
        cls.home = json.loads(cls.home_path.read_text(encoding='utf-8'))
        cls.studio_path = cls.root / 'content/studio.json'
        cls.studio = json.loads(cls.studio_path.read_text(encoding='utf-8'))
        cls.steps_path = cls.root / 'content/articles/wild-brow-9-steps.json'
        cls.steps = json.loads(cls.steps_path.read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.write(self.path, self.records)
        self.write(self.home_path, self.home)
        self.write(self.studio_path, self.studio)
        self.write(self.steps_path, self.steps)

    def write(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def build(self, success=True):
        run = subprocess.run([sys.executable, 'tools/build_brand.py'], cwd=self.root,
                             capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(run.returncode == 0, success, run.stdout + run.stderr)
        return run

    def source(self, path):
        return (self.root / path).read_text(encoding='utf-8')

    def record(self):
        return {'title':'CMS-TEST <script>unsafe()</script>', 'title_en':'CMS-TEST English',
                'alt':'CMS-TEST image', 'alt_en':'CMS-TEST image',
                'image':'/assets/hero-model.webp', 'description':'CMS-TEST description',
                'published':True, 'featured':True, 'featured_order':-100}

    def test_formal_philosophy_edits_reach_pages_and_machine_sources(self):
        studio=dict(self.studio)
        for suffix in ('', '_en'):
            studio['philosophy_style_body'+suffix]+='\n\nCMS philosophy paragraph'+suffix
            studio['philosophy_summary'+suffix]+=' CMS philosophy summary'+suffix
        self.write(self.studio_path,studio)
        self.build()
        for suffix,page,ai_path in (('', 'about.html','ai/summary.json'),('_en','en/about.html','ai/en.json')):
            source=self.source(page)
            visible=re.sub(r'<script.*?</script>','',source,flags=re.S)
            self.assertIn('CMS philosophy paragraph'+suffix,visible)
            self.assertIn('CMS philosophy summary'+suffix,visible)
            ai=json.loads(self.source(ai_path))['design_principles']
            self.assertEqual(ai['sections'][2]['paragraphs'][-1],'CMS philosophy paragraph'+suffix)
            self.assertEqual(ai['summary'],studio['philosophy_summary'+suffix])
            schemas=[json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>',source,re.S)]
            about=next(s for s in schemas if s['@type']=='AboutPage')
            self.assertEqual(about['abstract'],ai['summary'])
            self.assertIn('CMS philosophy paragraph'+suffix,about['hasPart'][2]['text'])
            self.assertIn(studio['philosophy_summary'+suffix],self.source('llms.txt'))

    def test_incomplete_formal_paragraphs_block_publication(self):
        studio=dict(self.studio)
        studio['philosophy_strokes_body']=studio['philosophy_strokes_body'].replace('\n\n',' ')
        self.write(self.studio_path,studio)
        result=self.build(success=False)
        self.assertIn('strokes',result.stderr)

    def test_repeated_build_preserves_generated_content(self):
        self.build()
        paths=[self.root / (route.lstrip('/') + ('index.html' if route.endswith('/') else ''))
               for route in json.loads(self.source('content/brand/routes.json'))]
        paths += list((self.root/'ai').glob('*.json'))
        paths += [self.root/path for path in ('.well-known/ai.txt','llms.txt','sitemap.xml','feed.xml')]
        before={path:path.read_bytes() for path in paths}
        self.build()
        self.assertEqual(before,{path:path.read_bytes() for path in paths})

    def test_publish_hide_and_delete_across_static_pages(self):
        record = self.record()
        self.write(self.path, [record] + self.records)
        self.build()
        for page in ('index.html','works.html','en/index.html','en/works.html'):
            source = self.source(page)
            self.assertIn('CMS-TEST', source)
            # JSON-LD may contain literal text, but its closing script marker
            # must be escaped. No executable script may reach the HTML body.
            visible_source = re.sub(r'<script type="application/ld\+json">.*?</script>', '', source, flags=re.S)
            self.assertNotIn('<script>unsafe()', visible_source)
        self.assertIn('&lt;script&gt;', self.source('works.html'))
        record['published'] = False
        self.write(self.path, [record] + self.records)
        self.build()
        for page in ('index.html','works.html','en/index.html','en/works.html'):
            self.assertNotIn('CMS-TEST', self.source(page))
        self.write(self.path, self.records)
        self.build()
        self.assertNotIn('CMS-TEST', self.source('works.html'))

    def test_video_with_cover_is_video_not_a_still_image(self):
        record = self.record()
        record.update(video='/assets/operation-brow.mp4', cover='/assets/operation-brow-poster.jpg')
        self.write(self.path, [record] + self.records)
        self.build()
        source = self.source('works.html')
        self.assertIn('poster="/assets/operation-brow-poster.jpg"', source)
        self.assertIn('<source src="/assets/operation-brow.mp4"', source)
        self.assertIn('"@type": "VideoObject"', source)
        self.assertIn('"contentUrl": "https://miaomeihuamu.com/assets/operation-brow.mp4"', source)

    def test_reordering_is_array_order(self):
        rows = list(reversed(self.records))
        self.write(self.path, rows)
        self.build()
        source = self.source('works.html').split('class="archive-grid"',1)[1]
        visible = [r for r in rows if r.get('published')]
        self.assertLess(source.index(visible[0]['image']), source.index(visible[-1]['image']))

    def test_optional_hero_and_procedure_media_can_be_removed(self):
        home = dict(self.home)
        home.pop('hero_image', None)
        home.pop('procedure_video', None)
        home['hero_title'] = 'CMS-TITLE\n第二行'
        home['hero_title_en'] = 'CMS-TITLE\nSecond line'
        self.write(self.home_path, home)
        self.build()
        for page in ('index.html','en/index.html'):
            source = self.source(page)
            self.assertIn('CMS-TITLE<br>', source)
            # The old anchor stays for inbound links; the image itself is gone.
            self.assertIsNone(re.search(r'<img\b[^>]*id="hero-image"', source))
            self.assertNotIn('<link rel="preload" as="image"', source)
            self.assertNotIn('/assets/operation-brow.mp4', source)

    def test_untrusted_media_and_missing_cover_block_build(self):
        for value in ('https://example.com/image.jpg','/assets/../content/home.json','/assets/missing.png'):
            record = self.record(); record['image'] = value
            self.write(self.path, [record] + self.records)
            self.build(False)
        record = self.record(); record.pop('image'); record['video']='/assets/operation-brow.mp4'
        self.write(self.path, [record] + self.records)
        self.assertIn('视频须设置封面', self.build(False).stderr)

    def test_optional_procedure_label_has_an_accessible_fallback(self):
        home = dict(self.home)
        home.pop('procedure_alt', None); home.pop('procedure_alt_en', None)
        self.write(self.home_path, home)
        self.build()
        self.assertIn('aria-label="本店操作过程记录"', self.source('index.html'))
        self.assertIn('aria-label="A studio procedure record"', self.source('en/index.html'))

    def test_replaced_video_does_not_inherit_the_old_upload_date(self):
        target = self.root / 'assets/uploads/videos/cms-new-video.mp4'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.root / 'assets/operation-brow.mp4', target)
        home = dict(self.home); home['procedure_video'] = '/assets/uploads/videos/cms-new-video.mp4'
        self.write(self.home_path, home)
        self.build()
        schemas = [json.loads(item) for item in re.findall(r'<script type="application/ld\+json">(.*?)</script>', self.source('index.html'), re.S)]
        video = next(item for item in schemas if item['@type'] == 'VideoObject')
        self.assertTrue(video['contentUrl'].endswith('/cms-new-video.mp4'))
        # This uncommitted fixture has no recorded upload date to publish.
        self.assertNotIn('uploadDate', video)

    def test_studio_photo_removal_updates_every_visible_use(self):
        studio = dict(self.studio); studio.pop('image', None)
        self.write(self.studio_path, studio)
        self.build()
        for page in ('index.html','about.html','area.html','en/index.html','en/about.html','en/area.html'):
            self.assertIsNone(re.search(r'<img\b[^>]*src="/assets/env/window.jpg"', self.source(page)), page)

    def test_step_images_stay_with_their_text_when_reordered(self):
        article = json.loads(json.dumps(self.steps))
        article['sections'][0], article['sections'][1] = article['sections'][1], article['sections'][0]
        self.write(self.steps_path, article)
        self.build()
        source = self.source('posts/wild-brow-9-steps.html')
        first = source.split('<section id="section-1">',1)[1].split('</section>',1)[0]
        self.assertIn(article['sections'][0]['title'], first)
        self.assertIn('/assets/9steps/step2.jpg', first)
        schemas = [json.loads(item) for item in re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)]
        howto = next(item for item in schemas if item['@type'] == 'HowTo')
        self.assertTrue(howto['step'][0]['image'].endswith('/step2.jpg'))

    def test_article_identifiers_cannot_escape_the_article_directory(self):
        article = dict(self.steps); article['slug'] = '../../admin/index'
        self.write(self.steps_path, article)
        self.assertIn('文章网址标识', self.build(False).stderr)

if __name__ == '__main__':
    unittest.main(verbosity=2)
