"""Live public hazard context; deliberately independent of operational scores."""
from datetime import datetime, timezone
import json
import math
import os
from .mapped_route import mapped_screen
from urllib.request import Request, urlopen
from .locations import check_location, load_catalog

USGS_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson'
WM_DOCS = 'https://github.com/koala73/worldmonitor/blob/main/docs/mcp-tools-reference.mdx'
MAX_BYTES = 2_000_000
LIMITATIONS = [
    'Earthquake context only: no flood, fire, conflict or transport disruption coverage is implied.',
    'Distance uses approximate corridor segments, not surveyed track or hazard impact footprints.',
    'Nearby events do not establish damage, rail closure or a predicted supply delay.',
    'No nearby reported events is not an all-clear. Reporting coverage and preliminary magnitudes can change.',
    'USGS is fetched directly, an upstream source also listed by World Monitor; this is not a World Monitor data feed.',
]


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _timestamp(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('Missing or invalid source timestamp')
    return datetime.fromtimestamp(value / 1000, timezone.utc)


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('Invalid numeric field')
    return value


def parse_usgs(payload, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(payload, dict) or payload.get('type') != 'FeatureCollection' or not isinstance(payload.get('features'), list):
        raise ValueError('Expected USGS GeoJSON FeatureCollection')
    generated = _timestamp(payload.get('metadata', {}).get('generated'))
    age = (now - generated).total_seconds()
    status = 'stale' if age > 1800 or age < -300 else 'ok'
    catalog = load_catalog()
    events, rejected = [], 0
    for feature in payload['features']:
        try:
            p, g = feature['properties'], feature['geometry']
            if g['type'] != 'Point':
                raise ValueError('Not a point')
            lon, lat = map(_number, g['coordinates'][:2])
            location = check_location(lat, lon, catalog)
            magnitude = _number(p['mag'])
            observed, updated = _timestamp(p['time']), _timestamp(p['updated'])
            if (observed - now).total_seconds() > 300 or (updated - now).total_seconds() > 300:
                raise ValueError('Future event timestamp')
            url = p.get('url', '')
            if not isinstance(url, str) or not url.startswith('https://earthquake.usgs.gov/'):
                url = 'https://earthquake.usgs.gov/earthquakes/map/'
            events.append({'id': str(feature['id']), 'title': str(p.get('place') or 'Unnamed earthquake'),
                'lat': lat, 'lon': lon, 'magnitude': magnitude, 'observed_at': _iso(observed),
                'updated_at': _iso(updated), 'url': url, 'source': 'USGS', 'source_id': 'usgs',
                'distance_km': location['nearest_segment']['distance_km'],
                'near_corridor': location['within_screening_buffer']})
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            rejected += 1
    events.sort(key=lambda e: (e['distance_km'], e['observed_at']))
    if rejected and status == 'ok':
        status = 'partial'
    return events, {'id': 'usgs', 'name': 'USGS earthquake catalogue · M2.5+ · past 7 days',
        'url': USGS_URL, 'status': status, 'generated_at': _iso(generated), 'fetched_at': _iso(now),
        'count': len(events), 'rejected_count': rejected,
        'error': f'{rejected} malformed event(s) excluded' if rejected else ('Feed timestamp is stale or future-dated' if status == 'stale' else None)}


def fetch_context(now=None):
    """Explicit refresh only. Timeout/size bounded; failure remains a visible gap."""
    now = now or datetime.now(timezone.utc)
    events = []
    try:
        request = Request(USGS_URL, headers={'User-Agent': 'AtlasIQ-local-prototype/1.0', 'Accept': 'application/geo+json,application/json'})
        with urlopen(request, timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Response exceeds size limit')
        events, source = parse_usgs(json.loads(raw), now)
    except Exception as exc:
        # Do not expose transport exception strings, credentials or raw responses.
        source = {'id': 'usgs', 'name': 'USGS earthquake catalogue · M2.5+ · past 7 days',
            'url': USGS_URL, 'status': 'error', 'generated_at': None, 'fetched_at': _iso(now),
            'count': 0, 'error': 'Source could not be fetched or validated (' + type(exc).__name__ + ')'}
    configured = bool(os.environ.get('WORLD_MONITOR_API_KEY', '').strip())
    return {'fetched_at': _iso(now), 'events': events, 'sources': [source],
        'world_monitor': {'status': 'configured_requires_request' if configured else 'unconfigured',
            'detail': 'World Monitor key detected; authenticated quota-consuming API calls are not enabled in this prototype.' if configured else 'World Monitor API key is not configured. Public upstream data is fetched directly from USGS.',
            'docs_url': WM_DOCS}, 'limitations': list(LIMITATIONS)}


def screen_mapped_notices(events):
    for event in events:
        if event.get('lon') is None or event.get('lat') is None:
            continue
        mapped = mapped_screen(event['lon'], event['lat'])
        event.update(distance_km=mapped['distance_km'], near_corridor=mapped['within_screening_buffer'],
                     mapped_section=mapped['section'], rail_layer_id=mapped['object_id'])


def fetch_all_context(now=None):
    """Collect independent context providers concurrently; each failure remains visible."""
    from concurrent.futures import ThreadPoolExecutor
    from .official_context import fetch_official_context
    from .rail_notices import fetch_rail_notices
    from .hotspots import fetch_hotspots
    now = now or datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=4) as pool:
        base = pool.submit(fetch_context, now)
        others = [(name, pool.submit(fn, now)) for name, fn in (
            ('Official WA/SA notices', fetch_official_context), ('Rail operator notices', fetch_rail_notices),
            ('DEA satellite hotspots', fetch_hotspots))]
        result = base.result()
        for name, future in others:
            try:
                events, sources = future.result()
                result['events'].extend(events)
                for source in sources:
                    source['max_age_minutes'] = source.get('max_age_seconds', 1800) / 60
                result['sources'].extend(sources)
            except Exception:
                result['sources'].append({'id': name, 'name': name, 'status': 'error', 'generated_at': None,
                    'fetched_at': _iso(now), 'count': 0, 'error': 'Provider could not be collected or validated.'})
    screen_mapped_notices(result['events'])
    result['limitations'] = [
        'Official notices are context for investigation, not a verified corridor closure or prediction.',
        'Point proximity uses the mapped Forrestfield–Port Augusta freight route; text place matches are candidates, not geographic intersections.',
        'Missing coordinates, publication times and unavailable feeds remain explicit gaps. No notices is not an all-clear.',
        'Road restrictions do not establish rail status. Consult the original authority before operational decisions.',
        'Public upstream sources are fetched directly; World Monitor hosted data is not connected.'
    ]
    result['world_monitor']['detail'] = 'Public upstream sources are used directly. World Monitor hosted data is not connected.'
    return result
