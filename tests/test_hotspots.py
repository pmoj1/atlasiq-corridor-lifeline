import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from corridor_lifeline.hotspots import fetch_hotspots, parse_hotspots

NOW = datetime(2026, 11, 8, 8, tzinfo=timezone.utc)


def feature(number=42, stamp='2026-11-08T03:00:00Z', coords=(122.5, -30.1)):
    return {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': coords},
            'properties': {'id': number, 'datetime': stamp, 'sensor': 'VIIRS', 'satellite': 'NOAA 21'}}


def payload(features, matched=None):
    return {'type': 'FeatureCollection', 'features': features, 'timeStamp': '2026-11-08T08:00:00Z',
            'numberMatched': len(features) if matched is None else matched, 'numberReturned': len(features)}


class HotspotTests(unittest.TestCase):
    def test_observation_provenance(self):
        events, source = parse_hotspots(payload([feature()]), NOW)
        self.assertEqual(source['status'], 'unknown')
        self.assertIsNone(source['generated_at'])
        self.assertEqual(events[0]['observed_at'], '2026-11-08T03:00:00Z')
        self.assertIsNone(events[0]['near_corridor'])
        self.assertEqual(events[0]['id'], 'dea:42')

    def test_partial_bounds_duplicates_and_expired(self):
        records = [feature(), feature(), feature(3, coords=(125, -25)),
                   feature(4, '2026-11-03T01:00:00Z'), feature(5, '2027-01-01T00:00:00Z')]
        events, source = parse_hotspots(payload(records, 7000), NOW)
        self.assertEqual(len(events), 1)
        self.assertEqual(source['rejected_count'], 4)
        self.assertIn('5 of 7000', source['error'])
        self.assertEqual(source['status'], 'partial')

    def test_stale_or_missing_count_and_empty(self):
        data = payload([], 'unknown')
        data['timeStamp'] = '2026-11-01T08:00:00Z'
        events, source = parse_hotspots(data, NOW)
        self.assertEqual(events, [])
        self.assertIn('stale', source['error'])
        self.assertEqual(source['status'], 'partial')
        self.assertEqual(parse_hotspots(payload([]), NOW)[1]['status'], 'unknown')

    def test_failure_and_inconsistent_counts(self):
        data = payload([feature()])
        data['numberReturned'] = 5
        with self.assertRaises(ValueError):
            parse_hotspots(data, NOW)
        with patch('corridor_lifeline.hotspots.urlopen', side_effect=TimeoutError()):
            events, sources = fetch_hotspots(NOW)
        self.assertEqual(events, [])
        self.assertEqual(sources[0]['status'], 'error')
        self.assertIsNone(sources[0]['generated_at'])
