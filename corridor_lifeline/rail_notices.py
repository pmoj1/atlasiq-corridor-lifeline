"""Public ARTC RSS news candidates, never verified operational rail status.

Only titles, original links and publication dates are retained. No article crawl.
The feed can contain corporate news and does not cover every operator or incident.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import re
import xml.etree.ElementTree as ET

ARTC_URL = 'https://www.artc.com.au/feed/'
MAX_BYTES = 2_000_000
KEYWORDS = ('kalgoorlie', 'nullarbor', 'cook', 'tarcoola', 'port augusta', 'east-west', 'east west')


def _iso(value):
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _date(value):
    result = parsedate_to_datetime(value or '')
    if result.tzinfo is None:
        raise ValueError('Publication date needs timezone')
    return result.astimezone(timezone.utc)


def parse_rail_notices(raw, now=None):
    now = now or datetime.now(timezone.utc)
    if len(raw) > MAX_BYTES or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Unsafe or oversized feed')
    root = ET.fromstring(raw)
    channel = root.find('channel')
    if root.tag != 'rss' or channel is None:
        raise ValueError('Expected RSS channel')
    generated = _date(channel.findtext('lastBuildDate') or channel.findtext('pubDate'))
    events, rejected = [], 0
    for item in channel.findall('item')[:20]:
        try:
            title = (item.findtext('title') or '').strip()
            url = (item.findtext('link') or '').strip()
            parsed = urlparse(url)
            published = _date(item.findtext('pubDate'))
            if not title or len(title) > 1000 or parsed.scheme != 'https' or parsed.hostname not in ('www.artc.com.au', 'artc.com.au') or parsed.username or parsed.password:
                raise ValueError('Invalid item')
            if (published - now).total_seconds() > 300:
                raise ValueError('Future publication')
            matches = [word for word in KEYWORDS if re.search(r'\b' + re.escape(word) + r'\b', title, re.I)]
            events.append({'id': 'artc:' + url, 'title': title, 'url': url,
                'source': 'ARTC operator news', 'source_id': 'artc_news', 'kind': 'rail_notice',
                'region': 'Australia', 'lat': None, 'lon': None, 'magnitude': None,
                'observed_at': _iso(published), 'updated_at': None,
                'distance_km': None, 'near_corridor': None,
                'candidate_places': matches, 'match_basis': 'Title place-name candidate: ' + ', '.join(matches) if matches else 'Unlocated operator news',
                'detail': 'Publication time only. Operator news candidate; does not establish an active disruption or verified rail status.'})
        except (ValueError, TypeError, OverflowError):
            rejected += 1
    age = (now - generated).total_seconds()
    status = 'stale' if age > 86400 or age < -300 else ('partial' if rejected else 'ok')
    source = {'id': 'artc_news', 'name': 'ARTC public operator news · not live rail status',
        'url': ARTC_URL, 'status': status, 'generated_at': _iso(generated), 'fetched_at': _iso(now),
        'count': len(events), 'rejected_count': rejected, 'max_age_seconds': 86400,
        'error': 'Publication feed is stale or future-dated; no current rail status inferred' if status == 'stale' else (f'{rejected} invalid notices excluded' if rejected else None),
        'limitations': 'Up to 20 ARTC news items only. Publication dates are not incident or verification times. No Arc Infrastructure coverage or all-clear inference.'}
    return events, source


def fetch_rail_notices(now=None):
    now = now or datetime.now(timezone.utc)
    try:
        request = Request(ARTC_URL, headers={'User-Agent': 'AtlasIQ-local-prototype/1.0', 'Accept': 'application/rss+xml,application/xml'})
        with urlopen(request, timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
        events, source = parse_rail_notices(raw, now)
        return events, [source]
    except Exception as exc:
        return [], [{'id': 'artc_news', 'name': 'ARTC public operator news · not live rail status',
            'url': ARTC_URL, 'status': 'error', 'generated_at': None, 'fetched_at': _iso(now),
            'count': 0, 'error': 'Operator news unavailable (' + type(exc).__name__ + '). Rail status remains unverified.'}]
