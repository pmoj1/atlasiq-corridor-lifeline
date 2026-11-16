"""Public Digital Earth Australia satellite thermal detections in the corridor region."""
from datetime import datetime, timezone
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .mapped_route import position

DOCS = 'https://knowledge.dea.ga.gov.au/data/product/dea-hotspots/'
CAP = 2000
MAX_BYTES = 2_000_000
WEST, SOUTH, EAST, NORTH = 115, -34, 139, -29
CRS = 'urn:ogc:def:crs:OGC:1.3:CRS84'
URL = 'https://hotspots.dea.ga.gov.au/geoserver/wfs?' + urlencode({
    'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
    'typeNames': 'public:hotspots_three_days', 'outputFormat': 'application/json',
    'srsName': CRS, 'bbox': f'{WEST},{SOUTH},{EAST},{NORTH},{CRS}',
    'propertyName': 'location,id,datetime,satellite,sensor,australian_state',
    'sortBy': 'datetime D,id A', 'count': CAP,
})


def utc_timestamp(text):
    if not isinstance(text, str):
        raise ValueError('Missing timestamp')
    result = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('UTC offset required')
    return result.astimezone(timezone.utc)


def iso(stamp):
    return stamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def source_record(now):
    return {
        'id': 'dea_hotspots', 'name': 'Digital Earth Australia Hotspots',
        'url': URL, 'provenance_url': DOCS, 'terms_url': DOCS, 'generated_at': None,
        'fetched_at': iso(now), 'count': 0, 'rejected_count': 0,
        'coverage': 'Past three days in 115–139°E and 29–34°S, newest detections first.',
        'licence_note': '© Commonwealth of Australia (Geoscience Australia), CC BY 4.0.',
        'limitations': 'Repeat thermal detections are possible. Coverage depends on satellite passes and cloud. No detections is not an all-clear.',
    }


def parse_hotspots(payload, now):
    if not isinstance(payload, dict) or payload.get('type') != 'FeatureCollection':
        raise ValueError('Expected WFS FeatureCollection')
    features = payload.get('features')
    if not isinstance(features, list) or len(features) > CAP:
        raise ValueError('Invalid feature list')
    returned = payload.get('numberReturned')
    if type(returned) is not int or returned != len(features):
        raise ValueError('Inconsistent WFS response count')
    matched = payload.get('numberMatched')
    if matched == 'unknown' or matched is None:
        matched = None
    elif type(matched) is not int or matched < returned:
        raise ValueError('Invalid WFS matched count')
    source = source_record(now)
    # WFS timeStamp is the query-response time, not a catalogue-update time.
    stamp = utc_timestamp(payload['timeStamp'])
    source['response_at'] = iso(stamp)
    seen, events = set(), []
    for f in features:
        try:
            props, geom = f['properties'], f['geometry']
            if geom['type'] != 'Point':
                raise ValueError('Expected detection point')
            pt = position(geom['coordinates'])
            lon, lat = pt['lon'], pt['lat']
            if not (WEST <= lon <= EAST and SOUTH <= lat <= NORTH):
                raise ValueError('Outside requested bounds')
            number = props['id']
            if type(number) is not int or number <= 0 or number in seen:
                raise ValueError('Invalid or repeated detection ID')
            observed = utc_timestamp(props['datetime'])
            # Each record retains its observation time. Expired/future observations stay excluded.
            if not -300 <= (now - observed).total_seconds() <= 3 * 86400:
                raise ValueError('Outside observation window')
            satellite, sensor = (str(props.get(k) or '').strip()[:64] for k in ('satellite', 'sensor'))
            region = str(props.get('australian_state') or '').strip() or 'Australia'
            title = 'Satellite hotspot detection' + (f' · {satellite}' if satellite else '')
            events.append({'id': f'dea:{number}', 'title': title, 'url': DOCS, 'source_id': 'dea_hotspots',
                           'source': 'Geoscience Australia · DEA Hotspots', 'kind': 'satellite_hotspot',
                           'region': region, 'lat': lat, 'lon': lon, 'magnitude': None,
                           'observed_at': iso(observed), 'updated_at': None, 'satellite': satellite,
                           'sensor': sensor, 'distance_km': None, 'near_corridor': None,
                           'detail': 'Satellite thermal detection. Fire identity, extent and rail impacts are unverified.'})
            seen.add(number)
        except (KeyError, TypeError, ValueError, OverflowError):
            source['rejected_count'] += 1
    issues = []
    if matched is None:
        issues.append('Publisher did not confirm total matching rows.')
    elif matched > returned:
        issues.append(f'Only {returned} of {matched} matching rows returned.')
    if not -300 <= (now - stamp).total_seconds() <= 1800:
        issues.append('WFS response timestamp is stale or future-dated.')
    if source['rejected_count']:
        issues.append(f"{source['rejected_count']} invalid, expired or duplicate rows excluded.")
    source.update(count=len(events), matched_count=matched, partial=bool(issues), retrieval_status='success',
                  status='partial' if issues else 'unknown',
                  error=' '.join(issues + ['Catalogue publication time unavailable.']))
    return events, source


def fetch_hotspots(now=None):
    now = now or datetime.now(timezone.utc)
    try:
        request = Request(URL, headers={'User-Agent': 'AtlasIQ-local-prototype/1.0', 'Accept': 'application/json'})
        with urlopen(request, timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Response exceeds byte limit')
        events, source = parse_hotspots(json.loads(raw), now)
    except Exception as exc:
        events = []
        source = source_record(now)
        source.update(status='error', retrieval_status='error',
                      error=f'Satellite detection data unavailable ({type(exc).__name__}).')
    return events, [source]
