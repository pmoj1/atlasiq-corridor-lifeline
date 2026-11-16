from datetime import datetime, timedelta, timezone
import unittest

from corridor_lifeline.weather import exposure, series, UNITS


class OutlookTests(unittest.TestCase):
    def test_partial_exposure(self):
        self.assertEqual(exposure(None, 4), 'unknown')
        self.assertEqual(exposure(None, 50), 'watch')
        self.assertEqual(exposure(4, 49), 'below threshold')

    def test_stale_and_missing(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        data = {k: [1] * 48 for k in UNITS}
        data['time'] = [(now + timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(48)]
        data['wind_speed_10m'][2] = None
        row = dict(latitude=-32, longitude=116, hourly_units=UNITS, hourly=data, utc_offset_seconds=0)
        site = dict(name='test', lat=-32, lon=116)
        self.assertEqual(series(row, site, now)['hours'][2]['exposure'], 'unknown')
        with self.assertRaises(ValueError):
            series(row, site, now + timedelta(days=1))
