"""Preview the homepage on loopback only, with an optional baseline checkout.

Run from any directory:
    python preview/serve.py --before ../website-rednotes-20261104

Uses Python's standard library. This is a local review server, not production.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, help='Path to the unchanged baseline checkout')
    parser.add_argument('--port', type=int, default=0, help='Loopback port; 0 chooses an available port')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    before = args.before.resolve() if args.before else None
    if before and not (before / 'index.html').is_file():
        parser.error('--before must point to a checkout containing index.html')

    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if before and path.startswith('/__before/'):
                original = self.directory
                self.directory = str(before)
                try:
                    return super().translate_path(path[len('/__before'):])
                finally:
                    self.directory = original
            return super().translate_path(path)

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Robots-Tag', 'noindex, nofollow')
            super().end_headers()

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(root))) as server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print(f'Homepage: {url}', flush=True)
        print(f'Desktop / mobile review: {url}preview/', flush=True)
        if before:
            print(f'Baseline: {url}__before/', flush=True)
        else:
            print('No --before checkout supplied; baseline comparison is unavailable.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
