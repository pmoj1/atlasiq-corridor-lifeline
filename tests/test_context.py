import copy
from datetime import datetime, timezone
import unittest
from unittest.mock import patch
from corridor_lifeline.context import parse_usgs, fetch_context


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 25, tzinfo=timezone.utc)
        ts = int(self.now.timestamp() * 1000)
        self.payload = {'type': 'FeatureCollection', 'metadata': {'generated': ts}, 'features': [
            {'id': 'test', 'geometry': {'type': 'Point', 'coordinates': [121.465, -30.748, 10]},
             'properties': {'mag': 3.2, 'place': 'Test event', 'time': ts - 10000, 'updated': ts,
                            'url': 'https://earthquake.usgs.gov/earthquakes/eventpage/test'}}]}

    def test_event_provenance_and_proximity(self):
        events, source = parse_usgs(self.payload, self.now)
        self.assertEqual(source['status'], 'ok')
        self.assertTrue(events[0]['near_corridor'])
        self.assertEqual(events[0]['source'], 'USGS')
        self.assertNotEqual(events[0]['observed_at'], source['fetched_at'])
        self.assertNotIn('score', events[0])

    def test_bad_coordinates_are_gap(self):
        for bad in [float('nan'), 1000, True, 'invalid']:
            payload = copy.deepcopy(self.payload)
            payload['features'][0]['geometry']['coordinates'][1] = bad
            events, source = parse_usgs(payload, self.now)
            self.assertEqual(events, [])
            self.assertEqual(source['status'], 'partial')
            self.assertEqual(source['rejected_count'], 1)

    def test_stale_and_future_feed(self):
        for delta in [-3600000, 3600000]:
            payload = copy.deepcopy(self.payload)
            payload['metadata']['generated'] += delta
            self.assertEqual(parse_usgs(payload, self.now)[1]['status'], 'stale')

    def test_network_failure_never_all_clear(self):
        with patch('corridor_lifeline.context.urlopen', side_effect=TimeoutError('secret')):
            result = fetch_context(self.now)
        self.assertEqual(result['sources'][0]['status'], 'error')
        self.assertEqual(result['events'], [])
        self.assertNotIn('secret', str(result))

    def test_invalid_and_empty_feed(self):
        with self.assertRaises(ValueError):
            parse_usgs({}, self.now)
        self.payload['features'] = []
        events, source = parse_usgs(self.payload, self.now)
        self.assertEqual(source['status'], 'ok')
        self.assertEqual(events, [])

    def test_future_event_excluded(self):
        self.payload['features'][0]['properties']['time'] += 3600000
        self.assertEqual(parse_usgs(self.payload, self.now)[1]['status'], 'partial')

if __name__ == '__main__':
    unittest.main()
