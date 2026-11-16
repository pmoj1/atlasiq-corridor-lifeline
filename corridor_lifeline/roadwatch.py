"""Local, recurring weather exposure checks for a planner-defined road segment."""
import copy
from datetime import datetime, timedelta, timezone
import json
import logging
import math
from pathlib import Path
from threading import Condition, Thread
from urllib.parse import urlencode
from urllib.request import urlopen

from .satellite import satellite
from .weather import MODEL, SOURCE, series

INTERVAL = 15
ROUTE_FILE = Path(__file__).resolve().parents[1] / 'config/road-watch-port-hedland.json'
MAPPED = json.loads(ROUTE_FILE.read_text())
VERTICES = MAPPED['geometry']['coordinates']
DEFAULT = {
    'road': MAPPED['properties']['name'],
    'permit': 'Contingency road access enquiry',
    'points': [dict(name=name,lat=xy[1],lon=xy[0]) for name,xy in zip(
        ['Mapped start','Mapped midpoint','Mapped end'],
        [VERTICES[0], VERTICES[len(VERTICES)//2], VERTICES[-1]])],
}


def validated(raw):
    def label(value):
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 160 or not value.strip().isprintable():
            raise ValueError('Provide a name between 1 and 160 printable characters.')
        return value.strip()

    if not isinstance(raw, dict) or not isinstance(raw.get('points'), list) or not 2 <= len(raw['points']) <= 12:
        raise ValueError('Provide 2–12 Australian road sampling points.')
    points = []
    for p in raw['points']:
        if not isinstance(p, dict):
            raise ValueError('Invalid road sampling point.')
        lat, lon = p.get('lat'), p.get('lon')
        if not all(type(v) in (int, float) and math.isfinite(v) for v in (lat, lon)) or not (-44 <= lat <= -9 and 112 <= lon <= 154):
            raise ValueError('Sampling point outside Australian mainland and Tasmania bounds.')
        points.append(dict(name=label(p.get('name')), lat=lat, lon=lon))
    if len({(p['lat'],p['lon']) for p in points}) != len(points) or len({p['name'] for p in points}) != len(points):
        raise ValueError('Each sampling point needs distinct coordinates and a unique name.')
    return dict(road=label(raw.get('road')), permit=label(raw.get('permit')), points=points)


def forecast_url(points):
    params = dict(latitude=','.join(str(p['lat']) for p in points),
                  longitude=','.join(str(p['lon']) for p in points),
                  hourly='temperature_2m,precipitation,wind_speed_10m', forecast_hours=48,
                  models='ecmwf_aifs025_single', timezone='GMT')
    return 'https://api.open-meteo.com/v1/forecast?' + urlencode(params)


def fetch_sites(points, now):
    with urlopen(forecast_url(points), timeout=12) as response:
        raw = response.read(250001)
    if len(raw) > 250000:
        raise ValueError('Oversize forecast')
    data = json.loads(raw)
    if not isinstance(data,list) or len(data) != len(points):
        raise ValueError('Incomplete road sampling network')
    return [series(row, point, now) for row, point in zip(data, points)]


def assess(config, sites, now, sat):
    windows = []
    missing = not sites
    for site in sites:
        window = None
        for h in site['hours']:
            missing |= h['rain_mm'] is None or h['wind_kmh'] is None
            if h['exposure'] != 'watch':
                window = None
                continue
            if window is None:
                window = dict(point=site['name'], start=h['time'], max_rain_mm=None, max_wind_kmh=None)
                windows.append(window)
            window['end'] = h['time']
            for k in ('rain_mm','wind_kmh'):
                if h[k] is not None:
                    prev = window['max_'+k]
                    window['max_'+k] = max(prev, h[k]) if prev is not None else h[k]
    status = 'watch' if windows else 'unknown' if missing else 'below threshold'
    detail = f'{len(windows)} forecast exposure window(s) at {len(sites)} sampled point(s).'
    if missing:
        detail += ' Forecast coverage incomplete.'
    draft = None
    if windows:
        evidence = '\n'.join(f"{w['point']} | {w['start']} to {w['end']} | peak hourly precipitation {w['max_rain_mm']} mm, sustained wind {w['max_wind_kmh']} km/h" for w in windows)
        draft = (f"PREPARATION DRAFT · HUMAN REVIEW REQUIRED\n{config['permit']}\nRoad: {config['road']}\nPrepared: {now.isoformat()}\n"
                 f"Times are model valid times; rain is the preceding hour accumulation and wind is instantaneous.\nReason: forecast exposure meets the planning threshold (5 mm/h precipitation or 50 km/h wind).\n{evidence}\n"
                 f"Forecast retrieved: {now.isoformat()}\nEvidence: {MODEL} via Open-Meteo · {forecast_url(config['points'])}\nRoad status: requires confirmation.\n"
                 "Complete: responsible authority, applicable permit, applicant, vehicle/load, alternate route, movement window and supporting evidence.\nSubmission: pending planner review.")
    return dict(status=status, checked_at=now.isoformat(), sites=sites, windows=windows, draft=draft, detail=detail,
                satellite_at=(sat.get('frames') or [{}])[-1].get('observed_at'), satellite_status=sat.get('status','unknown'),
                model=MODEL, source_url=SOURCE)


def check_notes(previous, current, points):
    notes = []
    if previous.get('status') != current['status']:
        notes.append(f"{previous.get('status', 'pending')} → {current['status']}")
    if previous.get('windows', []) != current['windows']:
        notes.append('Forecast exposure windows changed')
    if current['satellite_at'] and previous.get('satellite_at') != current['satellite_at']:
        notes.append('New satellite observation')
    gaps = []
    sites = {s['name']: s['hours'] for s in current['sites']}
    pixels = {p['name']: p['brightness'] for p in current['cloud_samples']}
    for point in points:
        name = point['name']
        hours = sites.get(name, [])
        for field, label in [('rain_mm', 'rain'), ('wind_kmh', 'wind')]:
            if len(hours) < 48 or any(h.get(field) is None for h in hours):
                gaps.append(name + ' ' + label)
        if pixels.get(name) is None:
            gaps.append(name + ' infrared')
    if gaps:
        notes.append('Missing or incomplete: ' + ', '.join(gaps))
    return notes or ['Same watch status, windows and scan']


def pending():
    return dict(status='pending',checked_at=None,sites=[],windows=[],draft=None,satellite_at=None,detail='Awaiting first check.')


class RoadWatch:
    def __init__(self, out):
        self.path = Path(out) / 'road-watch.json'
        self.lock = Condition()
        self.version = 0
        self.closed = False
        self.thread = None
        self.data = dict(config=copy.deepcopy(DEFAULT), current=pending(), history=[], interval_minutes=INTERVAL)
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text())
                saved['config'] = validated(saved['config'])
                if not isinstance(saved['history'], list) or not isinstance(saved['current'], dict):
                    raise ValueError('Invalid saved watch')
                self.data.update(saved)
            except (ValueError, TypeError, KeyError, OSError):
                logging.warning('Unreadable road watch state; using default configuration')
                self.path.rename(self.path.with_suffix('.invalid-' + str(int(datetime.now().timestamp()))))

    def close(self):
        with self.lock:
            self.closed = True
            self.lock.notify_all()
        if self.thread:
            self.thread.join(timeout=25)

    def save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data,allow_nan=False),encoding='utf-8')
        tmp.replace(self.path)
        self.data = data

    def start(self):
        with self.lock:
            if self.thread is None:
                self.thread = Thread(target=self.run, name='road-watch', daemon=True)
                self.thread.start()

    def status(self):
        with self.lock:
            result = copy.deepcopy(self.data)
        result['route'] = MAPPED if result['config']['points'] == DEFAULT['points'] and result['config']['road'] == DEFAULT['road'] else None
        stamp = result['current'].get('checked_at')
        if stamp and not timedelta(minutes=-5) <= datetime.now(timezone.utc)-datetime.fromisoformat(stamp) <= timedelta(minutes=INTERVAL*2):
            result['current'].update(status='unknown',detail='Last road check is stale or future dated.',draft=None, windows=[], sites=[])
        return result

    def configure(self, raw):
        config = validated(raw)
        with self.lock:
            self.save(dict(self.data, config=config, current=pending(), history=[]))
            self.version += 1
            self.lock.notify_all()
        return self.status()

    def run(self):
        while True:
            with self.lock:
                if self.closed:
                    return
                config, version = self.data['config'], self.version
            now = datetime.now(timezone.utc)
            try:
                sites = fetch_sites(config['points'], now)
            except (OSError, ValueError, TypeError, KeyError, IndexError):
                sites = []
            try:
                try:
                    scan = satellite()
                except Exception:
                    logging.exception('Satellite catalogue unavailable')
                    scan = {'status':'unavailable','frames':[]}
                result = assess(config, sites, now, scan)
                try:
                    from .road_cloud import cloud_samples
                    result['cloud_samples'] = cloud_samples(scan, config['points'])
                except Exception:
                    logging.exception('Road satellite pixel samples unavailable')
                    result['cloud_samples'] = []

                with self.lock:
                    if version != self.version:
                        continue
                    entry = {key:result[key] for key in ('checked_at','status','detail','satellite_at','draft')}
                    entry['notes'] = check_notes(self.data['current'], result, config['points'])
                    entry['windows'] = result['windows']
                    entry['previous_status'] = self.data['current']['status']
                    self.save(dict(self.data,current=result,history=([entry]+self.data['history'])[:96]))
            except Exception:
                logging.exception('Road watch could not complete or persist this check')
            with self.lock:
                self.lock.wait_for(lambda: self.closed or self.version != version, timeout=INTERVAL*60)
