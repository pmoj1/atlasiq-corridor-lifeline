import unittest
from datetime import datetime, timezone
from corridor_lifeline.roadwatch import DEFAULT, assess, validated


class RoadWatchTest(unittest.TestCase):
    def test_missing_forecast_has_no_draft(self):
        result=assess(DEFAULT,[],datetime.now(timezone.utc),{})
        self.assertEqual(result['status'],'unknown')
        self.assertIsNone(result['draft'])

    def test_exposure_creates_timed_review_draft(self):
        now=datetime(2026,11,9,tzinfo=timezone.utc)
        h=dict(time=now.isoformat(),rain_mm=8,wind_kmh=None,exposure='watch')
        result=assess(DEFAULT,[dict(name='Coolgardie',hours=[h])],now,{})
        self.assertEqual(result['windows'][0]['end'],'2026-11-09T00:00:00+00:00')
        self.assertIn('Coolgardie',result['draft'])
        self.assertIn('incomplete',result['detail'])

    def test_invalid_segment(self):
        with self.assertRaises(ValueError):
            validated(dict(DEFAULT,points=[DEFAULT['points'][0]]*2))
