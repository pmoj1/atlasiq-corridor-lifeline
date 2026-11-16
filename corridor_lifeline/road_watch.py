"""Point-forecast weather screening for a pinned public freight road section."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import math
import json

from .locations import _segment_distance
from .mapped_route import position
from .weather import exposure


ROUTE = Path(__file__).resolve().parent.parent / 'config/road-watch-port-hedland.json'
HOUR = timedelta(hours=1)


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Missing timestamp')
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise ValueError('Missing timezone')
    return date.astimezone(timezone.utc)


def reading(value):
    return value if type(value) in (float, int) and math.isfinite(value) and value >= 0 else None


def assess(forecast_payload, now=None):
    now = now or datetime.now(timezone.utc)
    road = json.loads(ROUTE.read_text())
    props = road['properties']
    lat, lon = props['sample_lat'], props['sample_lon']
    vertices = [position(p) for p in road['geometry']['coordinates']]
    km = min(_segment_distance(lat, lon, a, b) for a, b in zip(vertices, vertices[1:]))
    payload = forecast_payload or {}
    result = dict(route=road, status='unknown', checked_at=now.isoformat(),
                  forecast_fetched_at=payload.get('fetched_at'), model=payload.get('model'),
                  site=dict(name=props['site'], lat=lat, lon=lon, distance_km=round(km, 3)),
                  window_basis='First and last flagged hourly forecast timestamps (UTC). Precipitation is the preceding-hour total; wind is valid at the timestamp.',
                  windows=[], unknown_hours=48, reason='Fresh road-area forecast unavailable.')
    try:
        fetched = timestamp(payload.get('fetched_at'))
        if not -300 <= (now-fetched).total_seconds() <= 3600 or payload.get('status') not in ('ok','partial'):
            return result
        site = next(s for s in payload['sites'] if s['name'] == props['site'] and
                    s['lat'] == lat and s['lon'] == lon)
        first = now.replace(minute=0,second=0,microsecond=0)
        by_time = {timestamp(h['time']): h for h in site['hours']}
    except (KeyError, ValueError, TypeError, StopIteration):
        return result
    unknown = 0
    active = None
    for index in range(48):
        moment = first + index * HOUR
        hour = by_time.get(moment,{})
        rain, wind = reading(hour.get('rain_mm')), reading(hour.get('wind_kmh'))
        flag = exposure(rain, wind)
        if flag != 'watch':
            unknown += int(flag == 'unknown')
            active = None
            continue
        if active is None:
            active = dict(start=moment.isoformat(), peak_rain_mm=None, peak_wind_kmh=None, reasons=[])
            result['windows'].append(active)
        active['end'] = moment.isoformat()
        for key,value,limit,label in [('peak_rain_mm',rain,5,'Hourly precipitation ≥5 mm'),
                                      ('peak_wind_kmh',wind,50,'Sustained wind ≥50 km/h')]:
            if value is not None:
                active[key] = max(value, active[key] or 0)
                if value >= limit and label not in active['reasons']:
                    active['reasons'].append(label)
    result['unknown_hours'] = unknown
    if result['windows']:
        result.update(status='watch', reason='Forecast weather meets a planning threshold near the mapped freight road.')
    elif unknown:
        result['reason'] = 'Forecast coverage incomplete for this road.'
    else:
        result.update(status='below threshold', reason='All 48 forecast hours fall below the planning thresholds.')
    return result
