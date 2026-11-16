"""Read-only, loopback dashboard for a saved Corridor Lifeline result."""
import argparse
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
from urllib.parse import urlparse, parse_qs
from pathlib import Path

MAX_BYTES = 2_000_000


def text(value):
    return escape(str(value), quote=True)


def load_result(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Result exceeds the 2 MB limit')
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Expected a result object')
    for key in ('corridor', 'as_of', 'level', 'coverage'):
        if not isinstance(data.get(key), str):
            raise ValueError('Missing or invalid ' + key)
    if type(data.get('score')) is not int or not 0 <= data['score'] <= 100:
        raise ValueError('Invalid score')
    for key in ('reasons', 'issues', 'feeds', 'sources'):
        if not isinstance(data.get(key), list):
            raise ValueError('Missing or invalid ' + key)
    if not all(isinstance(feed, dict) for feed in data['feeds']):
        raise ValueError('Invalid feed entries')
    return data


def age_label(stamp, now, max_age_minutes):
    try:
        observed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if observed.tzinfo is None:
            raise ValueError()
        age = (now - observed).total_seconds()
    except (ValueError, TypeError, AttributeError):
        return 'UNKNOWN — invalid or missing timestamp'
    if age < -300:
        return 'UNKNOWN — timestamp is in the future'
    if age > max_age_minutes * 60:
        return f'STALE — saved result is {age / 3600:,.1f} hours old'
    return f'RECENT saved result — {max(0, age / 60):.0f} minutes old'


def listing(items):
    return '<ul>' + ''.join('<li>' + text(item) + '</li>' for item in items) + '</ul>'


def render(path, max_age_minutes=60, now=None, token="", mode="saved"):
    now = now or datetime.now(timezone.utc)
    views = (
        ('weather', 'National outlook', 'M4 13a4 4 0 0 1 1-8 5 5 0 0 1 9 2 3 3 0 0 1 1 6z'),
        ('context', 'Signals', 'M2 10h4l2-6 4 12 2-6h4'),
        ('earth', 'Site imagery', 'M2 7l8-4 8 4-8 4z M2 11l8 4 8-4 M2 15l8 4 8-4'),
    )
    nav = ''.join(f'<button id="nav-{key}" role="tab" aria-controls="{key}" aria-selected="{str(key == "weather").lower()}" data-view="{key}"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="{icon}"/></svg><span>{label}</span></button>' for key, label, icon in views)
    head = ('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AtlasIQ · Australia Operations</title><link rel="stylesheet" href="/assets/app.css"><link rel="stylesheet" href="/assets/studio.css"><link rel="stylesheet" href="/assets/weather.css"><link rel="stylesheet" href="/assets/road.css"></head><body>
<a class="skip" href="#workspace">Skip to workspace</a><aside class="rail-nav"><a class="studio-brand" href="/" aria-label="AtlasIQ home"><svg viewBox="48 40 225 240" aria-hidden="true"><polygon fill="#e9aa4b" points="160,57.6 256,262.4 209.92,262.4 160,155.904 110.08,262.4 64,262.4"/></svg>Atlas<span>IQ</span></a><div class="rail-rule"></div>
<p class="nav-kicker">WORKSPACE</p><div class="tabs studio-tabs" role="tablist" aria-label="Workspace">''' + nav + '''</div><div class="rail-end"><span class="rail-tag">AU</span><span>Australia Operations<small>Local workspace</small></span></div></aside>
<main class="studio-main" id="workspace" tabindex="-1"><div class="workspace-bar"><span>Workspace <b>/</b> <strong>Australian operations</strong></span><button type="button" onclick="location.reload()">Reload workspace</button></div><details class="regional-tools"><summary>East–west corridor tools</summary><a href="#locations">Rail alignment</a><a href="#overview">Assessment</a><a href="#evidence">Evidence</a><a href="#scenario">Supply scenario</a></details>''')
    try:
        data = load_result(path)
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        data = {'corridor': 'East–west corridor', 'as_of': '', 'score': 0, 'level': 'UNKNOWN', 'coverage': 'unavailable', 'reasons': [], 'issues': ['Result unavailable: ' + str(exc)], 'feeds': [], 'sources': []}
    controls = '<section class="panel monitor-controls"><p class="eyebrow">LOCAL OPERATIONS WORKSPACE</p><label>Assessment view <select id="assessment-mode"><option value="live">Current collection</option><option value="demo2024">Historical 2024 demonstration</option><option value="demo2022">Historical 2022 demonstration</option><option value="saved">Startup saved file</option></select></label><button id="collect-now">Check configured sources now</button><p id="collection-status" role="status">Explicit checks only. Weather and warning feeds are fetched; rail status comes from your manually verified file.</p><a href="/api/draft" download="corridor-alert.txt">Download latest current email draft</a><details><summary>Recent current collections</summary><p>Up to 100 recent entries shown; 1,000 retained locally. These are assessment scores, not probabilities. Historical demos are stored separately.</p><div id="assessment-history"></div></details></section>'
    age = age_label(data['as_of'], now, max_age_minutes)
    body = '<section id="overview" role="tabpanel" aria-labelledby="nav-overview" class="view" hidden><div class="section-heading"><div><p class="eyebrow">SAVED ASSESSMENT</p><h1>Corridor overview</h1></div></div>' + controls + '<section class="panel notice"><h2>' + text(age) + '</h2><p>Assessment time: ' + text(data['as_of']) + '</p><p>Age policy: stale after ' + text(max_age_minutes) + ' minutes; timestamps more than 5 minutes ahead are unknown. Historical source health is reported at assessment time, not reverified now.</p></section>'
    if data.get('fixture_note') or data.get('event_facts'):
        body += '<section class="panel notice"><h2>HISTORICAL DEMO — not live monitoring</h2><p>' + text(data.get('fixture_note', 'Historical scenario')) + '</p><p>Illustrative inputs do not demonstrate prediction accuracy.</p></section>'
    body += '<section class="panel"><h2>' + text(data['corridor']) + '</h2><div class="score">' + text(data['score']) + '/100</div><p>Saved level: <strong>' + text(data['level']) + '</strong> · Saved rail status: ' + text(data.get('rail_status', 'unknown')) + '</p><p>An explainable rule score, not a probability or an all-clear. Stale results do not establish current conditions.</p></section>'
    body += '<section class="panel notice"><h2>Coverage and data gaps</h2><p>' + text(data['coverage']) + '</p>' + listing(data['issues'] or ['No gaps reported at assessment time. This covers configured inputs only, not every corridor segment.']) + '</section>'
    body += component_chart(data)
    body += '<section class="panel reasons"><h2>Why this score</h2>' + listing(data['reasons']) + '<p>Rule version: ' + text(data.get('rule_version', 'unknown')) + '</p><pre>' + text(json.dumps(data.get('components', {}), indent=2)) + '</pre></section>'
    body += health_chart(data)
    body += '</section><section id="evidence" role="tabpanel" aria-labelledby="nav-evidence" class="view" hidden><div class="section-heading"><div><p class="eyebrow">TRACE EVERY SIGNAL</p><h2>Source evidence</h2></div><div class="filters"><input id="evidence-search" placeholder="Search evidence…" aria-label="Search evidence"><select id="evidence-filter" aria-label="Filter source health"><option value="all">All health states</option><option value="ok">Healthy at assessment</option><option value="other">Needs attention</option></select></div></div><p id="filter-count" aria-live="polite"></p><section class="panel">'
    for feed in data['feeds']:
        source_data = feed.get('data') if isinstance(feed.get('data'), dict) else {}
        body += '<article class="feed" data-health="' + text(feed.get('health', 'unknown')) + '"><h3>' + text(feed.get('name', 'Unnamed source')) + '</h3><dl>'
        for label, value in (
            ('Source', feed.get('source', 'Unknown')),
            ('Health at assessment', feed.get('health', 'unknown')),
            ('Observed / verified at', source_data.get('observed_at', 'Unknown')),
            ('Fetched at', feed.get('fetched_at', 'Unknown')),
        ):
            body += '<dt><strong>' + label + '</strong></dt><dd>' + text(value) + '</dd>'
        body += '</dl><details><summary>Inspect raw source evidence</summary><pre>' + text(json.dumps(feed, indent=2, ensure_ascii=False)) + '</pre></details></article>'
    body += listing(data['sources']) + '</section>'
    if data.get('event_facts'):
        body += '<section class="panel"><h2>Historical provenance</h2><pre>' + text(json.dumps(data['event_facts'], indent=2)) + '</pre></section>'
    scenario_path = Path(__file__).with_name('scenario.html')
    scenario = scenario_path.read_text() if scenario_path.exists() else '<p>Supply scenario is being prepared.</p>'
    payload = json.dumps(data).replace('<', '\\u003c')
    locations_path = Path(__file__).with_name('dashboard_assets') / 'locations.html'
    locations = locations_path.read_text() if locations_path.exists() else '<p>Location workspace unavailable.</p>'
    context_path = Path(__file__).with_name('dashboard_assets') / 'context.html'
    weather_html = (context_path.parent / "weather.html").read_text()
    weather_html += (context_path.parent / "road.html").read_text()
    earth_html = (context_path.parent / 'earth.html').read_text()
    context_html = context_path.read_text() if context_path.exists() else '<p>Context unavailable</p>'
    settings = json.dumps({'token': token, 'mode': mode}).replace('<', '\\u003c')
    return head + body + '</section><section id="context" role="tabpanel" aria-labelledby="nav-context" class="view" hidden>' + context_html + '</section><section id="weather" role="tabpanel" aria-labelledby="nav-weather" class="view">' + weather_html + '</section><section id="earth" class="view" hidden>' + earth_html + '</section><section id="locations" role="tabpanel" aria-labelledby="nav-locations" class="view" hidden>' + locations + '</section><section id="scenario" role="tabpanel" aria-labelledby="nav-scenario" class="view panel" hidden>' + scenario + '</section><footer><span>Local workspace · Review evidence before operational decisions · No alert delivery.</span><div><button id="export-result">Export assessment</button><button onclick="window.print()">Print brief</button></div></footer></main><script type="application/json" id="saved-result">' + payload + '</script><script type="application/json" id="workspace-settings">' + settings + '</script><script src="/assets/app.js"></script><script src="/assets/scenario.js"></script><script src="/assets/locations.js"></script><script src="/assets/monitor.js"></script><script src="/assets/context.js"></script><script src="/assets/weather.js"></script><script src="/assets/earth.js"></script><script src="/assets/road.js"></script></html>'



def component_chart(data):
    components = data.get('components', {})
    if not isinstance(components, dict):
        components = {}
    bars = ''
    for key in ('rainfall', 'warnings', 'rail'):
        value = components.get(key)
        valid = type(value) in (int, float) and 0 <= value <= 100
        bars += '<div class="bar-row"><span>' + key.title() + '</span><div class="bar-track"><i style="width:' + str(value if valid else 0) + '%"></i></div><b>' + text(value if valid else 'Unknown') + '</b></div>'
    return '<section class="panel component"><p class="eyebrow">EXPLAINABLE BY DESIGN</p><h2>Score breakdown</h2>' + bars + '<p class="muted">Component points are added, then capped at 100. This is a policy score, not a closure probability.</p></section>'


def health_chart(data):
    total = len(data['feeds'])
    healthy = sum(feed.get('health') == 'ok' for feed in data['feeds'])
    return '<section class="panel health"><p class="eyebrow">INPUT CONFIDENCE</p><h2>Source health</h2><div class="health-number">' + str(healthy) + '<span> / ' + str(total) + '</span></div><p>Sources healthy at assessment time</p><div class="bar-track"><i style="width:' + str(100 * healthy / total if total else 0) + '%"></i></div><p class="muted">' + str(total - healthy) + ' sources need attention. Historical health does not establish current freshness.</p></section>'



def make_handler(input_path, max_age_minutes, workspace, token):
    from .locations import load_catalog, check_location
    from .mapped_route import ROUTE_PATH, mapped_screen
    root = Path(__file__).resolve().parent.parent
    from threading import Lock
    from time import monotonic
    from .weather import forecast
    from .satellite import satellite
    feeds = {'/api/weather': forecast, '/api/satellite': satellite}
    feed_locks = {path: Lock() for path in feeds}
    cache = {}

    class Handler(BaseHTTPRequestHandler):
        def reply(self, value, status=200, content_type='application/json'):
            content = json.dumps(value, allow_nan=False).encode() if content_type == 'application/json' else value
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def allowed(self):
            port = self.server.server_port
            return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

        def do_GET(self):
            if not self.allowed():
                self.send_error(403)
                return
            request = urlparse(self.path)
            query = parse_qs(request.query)
            path = request.path
            try:
                if path == '/api/road-watch':
                    return self.reply(workspace.road_monitor.status())
                if path in feeds:
                    with feed_locks[path]:
                        expires, data = cache.get(path, (0, None))
                        if monotonic() >= expires:
                            data = feeds[path]()
                            ttl = 60 if data.get('status') in ('error', 'unavailable') else 300
                            cache[path] = monotonic() + ttl, data
                    return self.reply(data)
                if path == '/road-simulation':
                    return self.reply((root / 'output/road-simulation/index.html').read_bytes(), content_type='text/html; charset=utf-8')
                if path == '/rail-replay.csv':
                    return self.reply((root / 'research/rail-replay/replay-results.csv').read_bytes(), content_type='text/csv; charset=utf-8')
                if path == '/api/mapped-route':
                    return self.reply(ROUTE_PATH.read_bytes(), content_type='application/geo+json')
                if path == '/rail-replay':
                    report = Path(__file__).resolve().parent.parent / 'research/rail-replay/comparison.html'
                    return self.reply(report.read_bytes(), content_type='text/html; charset=utf-8')
                if path == '/api/context':
                    return self.reply(workspace.context_status())
                if path == '/api/locations':
                    return self.reply(load_catalog())
                if path == '/api/location-check':
                    if set(query) != {'lat', 'lon'} or any(len(v) != 1 for v in query.values()):
                        raise ValueError('Provide one latitude and longitude')
                    lat, lon = float(query['lat'][0]), float(query['lon'][0])
                    result = check_location(lat, lon)
                    result['mapped'] = mapped_screen(lon, lat)
                    return self.reply(result)
                if path == '/api/status':
                    return self.reply(workspace.status())
                if path == '/api/history':
                    return self.reply(workspace.history())
                if path == '/api/draft':
                    draft = workspace.out / 'alert.txt'
                    if not draft.exists():
                        return self.reply({'error': 'No current collection draft yet. Check sources first.'}, 404)
                    return self.reply(draft.read_bytes(), content_type='text/plain; charset=utf-8')
                assets = {'/assets/' + name: name for name in ('app.css', 'studio.css', 'app.js', 'scenario.js', 'locations.js', 'monitor.js', 'context.js', 'weather.js', 'weather.css', 'earth.js', 'road.js', 'road.css')}
                if path in assets:
                    asset = Path(__file__).with_name('scenario.js') if path == '/assets/scenario.js' else Path(__file__).with_name('dashboard_assets') / assets[path]
                    return self.reply(asset.read_bytes(), content_type='text/css' if asset.suffix == '.css' else 'text/javascript')
                if path not in ('/', '/index.html'):
                    return self.reply({'error': 'Not found'}, 404)
                mode = query.get('view', ['saved'])[0]
                paths = {'saved': input_path, 'live': workspace.out / 'latest.json', 'demo2024': root / 'output/demo/2024/latest.json', 'demo2022': root / 'output/demo/2022/latest.json'}
                if mode not in paths:
                    raise ValueError('Unknown assessment view')
                return self.reply(render(paths[mode], max_age_minutes, token=token, mode=mode).encode(), content_type='text/html; charset=utf-8')
            except (ValueError, OSError, KeyError) as exc:
                self.reply({'error': str(exc)}, 400)

        def do_POST(self):
            origin = self.headers.get('Origin')
            permitted = (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}')
            if not self.allowed() or origin not in permitted or self.headers.get('X-AtlasIQ-Token') != token:
                return self.reply({'error': 'Local workspace authorization required'}, 403)
            if self.path == '/api/road-watch':
                if self.headers.get_content_type() != 'application/json' or self.headers.get('Transfer-Encoding'):
                    return self.reply({'error': 'Send a JSON road configuration.'}, 400)
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 16384:
                        raise ValueError('Road configuration must be 1–16384 bytes.')
                    config = json.loads(self.rfile.read(length))
                    if not isinstance(config, dict):
                        raise ValueError('Expected a road configuration object.')
                    workspace.road_monitor.configure(config)
                    return self.reply(workspace.road_monitor.status(), 200)
                except (ValueError, KeyError, TypeError) as exc:
                    return self.reply({'error': str(exc)}, 400)
                except OSError:
                    return self.reply({'error': 'Could not save road configuration locally.'}, 503)
            if self.path not in ('/api/collect', '/api/context-refresh'):
                return self.reply({'error': 'Not found'}, 404)
            if self.headers.get('Content-Length', '0') != '0' or self.headers.get('Transfer-Encoding'):
                return self.reply({'error': 'This action accepts no request body'}, 400)
            if self.path == '/api/context-refresh':
                started = workspace.start_context()
                return self.reply({'started': started, **workspace.context_status()}, 202 if started else 409)
            started = workspace.start()
            self.reply({'started': started, **workspace.status()}, 202 if started else 409)
    return Handler


def main():
    from .workspace import Workspace
    parser = argparse.ArgumentParser(description='AtlasIQ local corridor workspace')
    root = Path(__file__).resolve().parent.parent
    parser.add_argument('--input', type=Path, default=root / 'output/live/latest.json')
    parser.add_argument('--config', type=Path, default=root / 'config/live.json')
    parser.add_argument('--out', type=Path, default=root / 'output/live')
    parser.add_argument('--port', type=int, default=8770)
    parser.add_argument('--max-age-minutes', type=int, default=60)
    args = parser.parse_args()
    if args.max_age_minutes <= 0:
        parser.error('--max-age-minutes must be positive')
    from .roadwatch import RoadWatch
    workspace = Workspace(args.config, args.out)
    workspace.road_monitor = RoadWatch(args.out)
    handler = make_handler(args.input, args.max_age_minutes, workspace, secrets.token_urlsafe(32))
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        workspace.road_monitor.start()
        print(f'Corridor workspace: http://127.0.0.1:{args.port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            workspace.road_monitor.close()


if __name__ == '__main__':
    main()
