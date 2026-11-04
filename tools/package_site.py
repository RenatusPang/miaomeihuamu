"""Package a validated static site without source, secrets or draft JSON."""
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / '_site'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def release_metadata():
    try:
        branch = os.environ.get('CMS_BRANCH') or os.environ.get('GITHUB_REF_NAME') or git('branch', '--show-current')
        revision = os.environ.get('CMS_REVISION') or git('rev-parse', 'HEAD')
    except subprocess.CalledProcessError:
        branch, revision = 'local-copy', 'local-copy'
    return {'repository': 'RenatusPang/miaomeihuamu', 'branch': branch,
            'revision': revision, 'built_at': datetime.now(timezone.utc).isoformat(),
            'preview': branch != 'main'}

def package():
    # This tool owns only the exact generated _site directory inside this repo.
    if TARGET.exists():
        if TARGET.is_symlink() or TARGET.resolve() != ROOT.resolve() / '_site':
            raise ValueError('Unsafe output directory')
        shutil.rmtree(TARGET)
    TARGET.mkdir()
    for path in ROOT.glob('*.html'):
        shutil.copy2(path, TARGET / path.name)
    for name in ('en', 'posts', 'assets', 'ai', '.well-known', 'admin'):
        shutil.copytree(ROOT / name, TARGET / name)
    for name in ('CNAME', 'robots.txt', 'sitemap.xml', 'feed.xml', 'llms.txt', '.nojekyll'):
        path = ROOT / name
        if path.is_file():
            shutil.copy2(path, TARGET / name)
    release = release_metadata()
    if release['preview']:
        for path in TARGET.rglob('*.html'):
            source = path.read_text(encoding='utf-8')
            source = re.sub(r'<meta\s+name=["\']robots["\'][^>]*>', '', source, flags=re.I)
            path.write_text(source.replace('</head>', '<meta name="robots" content="noindex,nofollow"></head>'), encoding='utf-8')
        (TARGET / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    (TARGET / 'admin/release.json').write_text(json.dumps(release, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(release))

if __name__ == '__main__':
    package()
