"""Keep a loopback-only preview in sync with the isolated CMS branch.

The working checkout is never reset or overwritten. Each revision is built in
an owned cache directory, validated, then selected atomically for serving.
Only generated snapshots created by this tool are eligible for cache cleanup.
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()
STATE = {}
STOP = threading.Event()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.PIPE, timeout=45).decode().strip()


def update(branch, cache):
    global STATE
    git('fetch', '--no-tags', 'origin', f'refs/heads/{branch}:refs/remotes/origin/{branch}')
    revision = git('rev-parse', f'refs/remotes/origin/{branch}')
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Unexpected revision')
    with LOCK:
        if STATE.get('revision') == revision and Path(STATE['directory']).is_dir():
            STATE['error'] = ''
            return
    snapshot = (cache / revision).resolve()
    if snapshot.parent != cache or snapshot.is_symlink():
        raise ValueError('Unsafe cache path')
    marker = snapshot / '.cms-preview-owned'
    if snapshot.exists() and not marker.is_file():
        raise ValueError('Refusing to overwrite an unowned directory')
    snapshot.mkdir(parents=True, exist_ok=True)
    marker.write_text(revision, encoding='ascii')
    archive = subprocess.check_output(['git','archive','--format=tar',revision],cwd=ROOT,timeout=45)
    with tarfile.open(fileobj=io.BytesIO(archive)) as files:
        for entry in files.getmembers():
            if entry.issym() or entry.islnk() or not (snapshot / entry.name).resolve().is_relative_to(snapshot):
                raise ValueError('Unsafe archive member')
        files.extractall(snapshot, filter='data')
    environment = dict(os.environ)
    environment.update(CMS_BRANCH=branch, CMS_REVISION=revision,
                       CMS_CONTENT_DATE=git('show','-s','--format=%cs',revision),
                       GIT_DIR=git('rev-parse','--absolute-git-dir'), GIT_WORK_TREE=str(snapshot), PYTHONUTF8='1')
    for script in ('build_brand.py','verify_brand.py','package_site.py'):
        result = subprocess.run([sys.executable, f'tools/{script}'],cwd=snapshot,env=environment,
                                capture_output=True,text=True,encoding='utf-8',timeout=60)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout)[-1600:])
    with LOCK:
        STATE = {'revision':revision,'branch':branch,'directory':str(snapshot/'_site'),'error':''}
    print(f'Preview updated: {revision[:12]}', flush=True)
    # Keep the current snapshot and one previous snapshot. Never delete an
    # arbitrary cache child or follow a symlink outside this owned cache.
    owned = sorted((p for p in cache.iterdir() if p.is_dir() and not p.is_symlink()
                    and re.fullmatch(r'[0-9a-f]{40}',p.name) and (p/'.cms-preview-owned').is_file()),
                   key=lambda p:p.stat().st_mtime,reverse=True)
    for old in owned[2:]:
        if old.resolve().parent != cache or old.name == revision:
            continue
        shutil.rmtree(old)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        with LOCK:
            directory = STATE['directory']
        super().__init__(*args,directory=directory,**kwargs)

    def do_GET(self):
        if urlsplit(self.path).path == '/__cms_preview_status':
            with LOCK:
                data = {k:v for k,v in STATE.items() if k != 'directory'}
            payload = json.dumps(data).encode()
            self.send_response(200); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(payload))); self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Robots-Tag','noindex, nofollow')
        super().end_headers()

    def log_message(self,*args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch',default='codex/owner-cms-20261104')
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--interval',type=int,default=30)
    args = parser.parse_args()
    if not re.fullmatch(r'codex/owner-cms-[A-Za-z0-9-]+', args.branch):
        parser.error('This preview watches only an isolated owner-cms branch')
    cache = args.cache.resolve()
    if cache == ROOT or ROOT.is_relative_to(cache):
        parser.error('Use a separate generated cache directory')
    cache.mkdir(parents=True,exist_ok=True)
    update(args.branch,cache)
    def watch():
        while not STOP.wait(max(15,args.interval)):
            try:
                update(args.branch,cache)
            except Exception as error:
                with LOCK:
                    STATE['error'] = str(error)[:1600]
                print('Preview kept its last valid version: '+str(error)[:300],flush=True)
    threading.Thread(target=watch,daemon=True).start()
    server = ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Automatic CMS preview: http://127.0.0.1:{server.server_port}/',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        STOP.set(); server.server_close()

if __name__ == '__main__':
    main()
