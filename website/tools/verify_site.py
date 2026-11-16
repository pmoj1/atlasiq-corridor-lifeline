"""Validate the static website's local resources and navigation before packaging."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from collections import Counter
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'draft'
NODE = Path('/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs, self.images, self.buttons = [], [], [], []
        self.lang = None

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'html':
            self.lang = attrs.get('lang')
        if tag == 'img':
            self.images.append(attrs)
        if tag == 'button':
            self.buttons.append(attrs)
        for attr in ['src', 'href', 'poster']:
            if attrs.get(attr):
                self.refs.append(attrs[attr])
        if attrs.get('srcset'):
            self.refs.extend(part.strip().split()[0] for part in attrs['srcset'].split(','))


pages, errors = {}, []
for path in SITE.rglob('*.html'):
    page = Page()
    page.feed(path.read_text())
    pages[path] = page
    duplicates = [key for key, n in Counter(page.ids).items() if n > 1]
    if duplicates:
        errors.append(f'{path.name}: duplicate IDs {duplicates}')
    if not page.lang:
        errors.append(f'{path.name}: missing page language')
    if any('alt' not in attrs for attrs in page.images):
        errors.append(f'{path.name}: image without alt attribute')

reference_count = 0
for path, page in pages.items():
    for ref in page.refs:
        parsed = urlsplit(ref)
        if parsed.scheme or parsed.netloc:
            continue
        reference_count += 1
        if parsed.path:
            target = ((SITE if parsed.path.startswith('/') else path.parent) / unquote(parsed.path).lstrip('/')).resolve()
            if target.is_dir():
                target = target / 'index.html'
        else:
            target = path
        if not target.exists():
            errors.append(f'{path.relative_to(SITE)}: missing {ref}')
        elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
            errors.append(f'{path.relative_to(SITE)}: missing fragment {ref}')

for path in SITE.rglob('*.css'):
    for ref in re.findall(r'url\([\s\"\']*([^\)\"\']+)', path.read_text()):
        if not urlsplit(ref).scheme and not (path.parent / ref).resolve().exists():
            errors.append(f'{path.relative_to(SITE)}: missing CSS resource {ref}')

for path in SITE.rglob('*.js'):
    result = subprocess.run([str(NODE), '--check', str(path)], capture_output=True, text=True)
    if result.returncode:
        errors.append(result.stderr)

legacy = re.compile(r'Jake Bishop|Aone Senai|AtlasIQ\s*(?:&nbsp;)?\s*(?:Extract|Comply)|customs automation|order.entry agent', re.I)
for path in [*SITE.rglob('*.html'), *SITE.rglob('*.js')]:
    if legacy.search(path.read_text()):
        errors.append(f'{path.relative_to(SITE)}: legacy product or founder reference')

report = {'pages': len(pages), 'local_references': reference_count, 'javascript_syntax': 'passed' if not errors else 'see errors', 'errors': errors}
print(json.dumps(report, indent=2))
raise SystemExit(bool(errors))
