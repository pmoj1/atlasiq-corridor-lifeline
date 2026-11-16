"""Small read-only adapters. Failure is data, never a zero-risk observation."""
import json
import math
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from http.client import HTTPException

UTC = timezone.utc
MAX_BYTES = 2_000_000


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamp must include a timezone')
    return result.astimezone(UTC)


def text(value):
    return ' '.join(unescape(re.sub(r'<[^>]+>', ' ', str(value))).split())


def read(source, base):
    if urlparse(source).scheme in ('http', 'https'):
        request = Request(source, headers={'User-Agent': 'AtlasIQ-Corridor-Lifeline/0.1'})
        with urlopen(request, timeout=20) as response:
            data = response.read(MAX_BYTES + 1)
    else:
        data = (base / source).read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError('source exceeds 2 MB limit')
    return data


def weather(data, spec):
    rows = json.loads(data)['observations']['data']
    if not rows:
        raise ValueError('empty observation series')
    row = max(rows, key=lambda r: r['aifstime_utc'])
    observed = datetime.strptime(row['aifstime_utc'], '%Y%m%d%H%M%S').replace(tzinfo=UTC)
    rain = row.get('rain_trace')
    if rain in (None, '-', ''):
        raise ValueError('rainfall missing')
    rain = float(rain)
    if not math.isfinite(rain) or rain < 0:
        raise ValueError('invalid rainfall')
    return {'observed_at': observed.isoformat(), 'rain_since_9am_mm': rain,
            'station': text(row.get('name', spec['name']))}


def warnings(data, spec):
    root = ET.fromstring(data)
    channel = root.find('channel')
    if root.tag != 'rss' or channel is None:
        raise ValueError('expected RSS channel')
    # Feed publication time is not a fetch time. Old feeds are not silently fresh.
    published = channel.findtext('lastBuildDate') or channel.findtext('pubDate')
    if not published:
        raise ValueError('RSS channel publication time missing')
    observed = parsedate_to_datetime(published)
    if observed.tzinfo is None:
        raise ValueError('RSS timestamp must include timezone')
    items = []
    for item in channel.findall('item'):
        title = text(item.findtext('title', ''))
        description = text(item.findtext('description', ''))
        # Keep all state-wide items: RSS often omits district names.
        items.append({'title': title, 'description': description,
                      'url': text(item.findtext('link', spec['source']))})
    return {'observed_at': observed.isoformat(), 'items': items}


def rail(data, spec):
    row = json.loads(data)
    if not isinstance(row, dict):
        raise ValueError('rail input must be a JSON object')
    if row['corridor_id'] != spec['corridor_id']:
        raise ValueError('rail corridor_id does not match configuration')
    if row['status'] not in ('open', 'restricted', 'closed', 'unknown'):
        raise ValueError('rail status must be open, restricted, closed or unknown')
    timestamp(row['observed_at'])
    if not all(isinstance(row.get(k), str) and row[k].strip() for k in ('source_url', 'summary', 'observed_at')):
        raise ValueError('rail source_url and summary are required')
    return {key: row[key] for key in ('observed_at', 'status', 'source_url', 'summary')}


PARSERS = {'weather': weather, 'warnings': warnings, 'rail': rail}


def collect(config, base, now):
    results = []
    for spec in config['sources']:
        result = {'name': spec['name'], 'kind': spec['kind'],
                  'source': spec['source'], 'fetched_at': now.isoformat()}
        try:
            result['data'] = PARSERS[spec['kind']](read(spec['source'], base), spec)
            age = (now - timestamp(result['data']['observed_at'])).total_seconds()
            if age < -300:
                raise ValueError('source timestamp is in the future')
            result['health'] = 'stale' if age > spec['max_age_minutes'] * 60 else 'ok'
            if result['health'] == 'stale':
                result['error'] = f'source is {age / 3600:.1f} hours old'
        except (OSError, ValueError, KeyError, TypeError, AttributeError, HTTPException, ET.ParseError) as exc:
            result['health'] = 'error'
            result['error'] = str(exc) or type(exc).__name__
        results.append(result)
    return results
