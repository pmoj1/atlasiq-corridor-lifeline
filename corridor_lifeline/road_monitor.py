"""Periodic weather screening for the local logistics preparation desk."""
import json
import threading
from collections import deque
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .weather import forecast
from .satellite import satellite
from .road_watch import assess


class RoadMonitor:
    interval = 600

    def __init__(self, directory):
        self.path = Path(directory) / 'road-watch-history.json'
        try:
            saved = json.loads(self.path.read_text())
            if not isinstance(saved, list):
                saved = []
        except (OSError, ValueError):
            saved = []
        self.history = deque((x for x in saved if isinstance(x, dict)), maxlen=144)
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.latest = {'status': 'starting', 'windows': [], 'reason': 'First check in progress.'}

    def check(self):
        now = datetime.now(timezone.utc)
        try:
            result = assess(forecast(), now)
        except Exception:
            result = {'status':'unknown', 'windows':[], 'reason':'Road forecast screening unavailable.'}
        try:
            scan = satellite()
            frames = scan.get('frames') or [{}]
            result.update(satellite_status=scan['status'], satellite_observed_at=frames[-1].get('observed_at'))
        except Exception:
            result.update(satellite_status='unavailable', satellite_observed_at=None)
        result['checked_at'] = now.isoformat()
        entry = {key: result.get(key) for key in ('checked_at','status','reason','satellite_observed_at')}
        entry['watch_windows'] = len(result['windows'])
        if result.get('status') == 'watch':
            road = result['route']['properties']
            entry['draft'] = '\n'.join([
                'PERMIT PREPARATION · UNVERIFIED · INTERNAL REVIEW',
                'Road: ' + road['name'], 'Checked: ' + entry['checked_at'],
                'Forecast retrieved: ' + str(result.get('forecast_fetched_at')),
                'Satellite observation: ' + str(result.get('satellite_observed_at')),
                'Road evidence: ' + road['source_url'],
                *[f"{w['start']} to {w['end']} | rain {w['peak_rain_mm']} mm/h | wind {w['peak_wind_kmh']} km/h" for w in result['windows']],
                'Operator confirmation: pending', 'Shipment / applicant: pending',
                'Vehicle and load: pending', 'Proposed route and timing: pending',
                'Permit type, issuing authority and requirements: to be confirmed',
                'Prepared for review. No application submitted.',
            ])
        with self.lock:
            self.history.appendleft(entry)
            self.latest = result
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix('.tmp')
                tmp.write_text(json.dumps(list(self.history)))
                tmp.replace(self.path)
            except OSError:
                self.latest['history_warning'] = 'Check history available in memory only.'

    def run(self):
        while not self.stop.is_set():
            self.check()
            self.stop.wait(self.interval)

    def snapshot(self):
        with self.lock:
            result = dict(self.latest, history=list(self.history), interval_seconds=self.interval)
        if result.get('checked_at'):
            age = datetime.now(timezone.utc) - datetime.fromisoformat(result['checked_at'])
            if age > timedelta(seconds=self.interval * 2) or age < timedelta(0):
                result.update(status='unknown', windows=[], reason='Latest monitor check is stale or future dated.')
        return result
