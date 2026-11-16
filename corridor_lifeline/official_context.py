"""Official contextual notices. These never establish rail operating status."""
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor
import json
import re
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from .locations import check_location

ROAD = 'https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/Apps/TravelMap/MapServer/0'
DFES = 'https://services-ap1.arcgis.com/2FUMGdjxkn90jKLQ/ArcGIS/rest/services/DFES%20EmergencyWA%20Warning%20Points%20%28DFES-070%29/FeatureServer'
SPECS = [
    ('mrwa', 'Main Roads WA road incidents', ROAD + '/query?where=publishExternally%3D%27Yes%27&outFields=*&outSR=4326&f=json&resultRecordCount=2000', 'WA', 'https://catalogue.data.wa.gov.au/dataset/mrwa-webeoc-road-incidents'),
    ('bom_wa', 'BOM WA land warnings', 'https://www.bom.gov.au/fwo/IDZ00067.warnings_land_wa.xml', 'WA', 'https://www.bom.gov.au/rss/'),
    ('bom_sa', 'BOM SA land warnings', 'https://www.bom.gov.au/fwo/IDZ00064.warnings_land_sa.xml', 'SA', 'https://www.bom.gov.au/rss/'),
    ('dfes', 'DFES EmergencyWA warning points', DFES + '?f=json', 'WA', 'https://www.dfes.wa.gov.au/emergencywa/faq'),
]
PLACES = ('Perth', 'Kalgoorlie', 'Rawlinna', 'Tarcoola', 'Port Augusta', 'Eucla', 'Goldfields', 'North West Pastoral')


def iso(d):
    return d.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def timestamp(value, road=False):
    if not value:
        return None
    try:
        d = datetime.strptime(value, '%d/%m/%Y %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=8))) if road else parsedate_to_datetime(value)
        return iso(d) if d.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def _event(identity, title, source, region, kind, observed=None, updated=None, lat=None, lon=None, url=None, detail=''):
    event = dict(id=identity, title=title, source=source, source_id=source, region=region, kind=kind,
        hazard_type=kind.replace('_', ' '), magnitude=None, observed_at=observed, updated_at=updated,
        lat=None, lon=None, distance_km=None, near_corridor=None, match_basis='unlocated', candidate_places=[],
        url=url, detail=detail)
    if lat is not None and lon is not None:
        screening = check_location(lat, lon)
        event.update(lat=lat, lon=lon, distance_km=screening['nearest_segment']['distance_km'],
            near_corridor=screening['within_screening_buffer'], match_basis='approximate_point_distance')
    else:
        event['candidate_places'] = [p for p in PLACES if re.search(r'\b' + re.escape(p) + r'\b', title + ' ' + detail, re.I)]
        if event['candidate_places']:
            event['match_basis'] = 'text_candidate'
    return event


def parse_road(payload):
    if not isinstance(payload, dict) or 'error' in payload or not isinstance(payload.get('features'), list):
        raise ValueError('Invalid ArcGIS features')
    events, rejected = [], 0
    sr = payload.get('spatialReference', {}).get('latestWkid', payload.get('spatialReference', {}).get('wkid'))
    if sr != 4326:
        raise ValueError('Expected WGS84 point coordinates')
    for f in payload['features']:
        try:
            p, g = f['attributes'], f.get('geometry') or {}
            if p.get('publishExternally') != 'Yes':
                continue
            title = str(p.get('Location') or p.get('Road') or 'Road incident').strip()
            e = _event('mrwa:' + str(p['Id']), title, 'mrwa', 'WA', 'road_incident',
                timestamp(p.get('EntryDate'), True), timestamp(p.get('UpdateDateTime'), True),
                g.get('y'), g.get('x'), 'https://travelmap.mainroads.wa.gov.au/Home/Map',
                ' · '.join(str(p.get(k) or '') for k in ('IncidentType', 'ClosureType', 'TrafficCondition', 'TrafficImpact')))
            e['hazard_type'] = p.get('IncidentType') or 'Road incident'
            events.append(e)
        except (ValueError, KeyError, TypeError):
            rejected += 1
    return events, None, rejected, bool(payload.get('exceededTransferLimit'))


def parse_bom(raw, source, region):
    channel = ET.fromstring(raw).find('channel')
    if channel is None:
        raise ValueError('Expected RSS channel')
    generated = timestamp(channel.findtext('lastBuildDate') or channel.findtext('pubDate'))
    events = []
    for i, item in enumerate(channel.findall('item')):
        title = item.findtext('title') or 'Untitled warning'
        url = item.findtext('link') or 'https://www.bom.gov.au/weather/warnings.shtml'
        if not re.match(r'^https?://(?:www\.)?bom\.gov\.au/', url):
            url = 'https://www.bom.gov.au/weather/warnings.shtml'
        events.append(_event(source + ':' + str(i), title, source, region, 'weather_warning',
            timestamp(item.findtext('pubDate')), timestamp(item.findtext('pubDate')), url=url,
            detail=re.sub('<[^>]*>', '', item.findtext('description') or '')[:3000]))
    return events, generated, 0, False


def _fetch(spec, now):
    sid, name, url, region, provenance = spec
    source = dict(id=sid, name=name, url=url, provenance_url=provenance, terms_url=provenance,
        region=region, generated_at=None, fetched_at=iso(now), status='unknown', retrieval_status='error',
        count=0, rejected_count=0, max_age_seconds=10800, coverage='WA road point notices' if sid == 'mrwa' else region + ' published warnings',
        licence_note='BOM RSS is restricted to personal/non-commercial use.' if sid.startswith('bom') else 'Official public endpoint; check publisher terms before commercial distribution.')
    try:
        with urlopen(Request(url, headers={'User-Agent': 'AtlasIQ-local-prototype/1.0'}), timeout=12) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Response size exceeded')
        if sid == 'dfes':
            payload = json.loads(raw)
            if not payload.get('layers'):
                raise ValueError('Official warning service exposes no queryable layers')
            raise ValueError('Warning service schema requires verification before enabling')
        events, generated, rejected, partial = parse_road(json.loads(raw)) if sid == 'mrwa' else parse_bom(raw, sid, region)
        source.update(retrieval_status='success', generated_at=generated, count=len(events), rejected_count=rejected,
            partial=partial or bool(rejected))
        if generated:
            age = (now - datetime.fromisoformat(generated.replace('Z', '+00:00'))).total_seconds()
            source['status'] = 'stale' if age > 10800 or age < -300 else 'ok'
        if partial or rejected:
            source['status'] = 'partial'
            source['error'] = 'Incomplete result: transfer limit or malformed records; no all-clear can be inferred.'
        elif not generated:
            source['error'] = 'Retrieved successfully; publisher supplies no feed publication timestamp. Freshness unknown.'
        else:
            source['error'] = 'Feed publication time is stale or future-dated.' if source['status'] == 'stale' else None
        return events, source
    except Exception as exc:
        source.update(status='error', error=('Official DFES service has no verified queryable layer; consult EmergencyWA directly.' if sid == 'dfes' else 'Source unavailable or invalid (' + type(exc).__name__ + ').'))
        return [], source


def fetch_official_context(now=None):
    now = now or datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda spec: _fetch(spec, now), SPECS))
    return [e for events, _ in results for e in events], [source for _, source in results]
