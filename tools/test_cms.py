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

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.write(self.path, self.records)
        self.write(self.home_path, self.home)

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
            self.assertNotIn('as="image" href="/assets/hero-model.webp"', source)
            self.assertNotIn('/assets/operation-brow.mp4', source)

    def test_untrusted_media_and_missing_cover_block_build(self):
        for value in ('https://example.com/image.jpg','/assets/../content/home.json','/assets/missing.png'):
            record = self.record(); record['image'] = value
            self.write(self.path, [record] + self.records)
            self.build(False)
        record = self.record(); record.pop('image'); record['video']='/assets/operation-brow.mp4'
        self.write(self.path, [record] + self.records)
        self.assertIn('视频须设置封面', self.build(False).stderr)

if __name__ == '__main__':
    unittest.main(verbosity=2)
