import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from corridor_lifeline.rail_notices import parse_rail_notices, fetch_rail_notices, MAX_BYTES

NOW = datetime(2026, 10, 25, tzinfo=timezone.utc)

def feed(date='Sat, 24 Oct 2026 23:00:00 +0000', link='https://www.artc.com.au/news/test'):
    return f'<rss><channel><lastBuildDate>{date}</lastBuildDate><item><title>East-west work update</title><link>{link}</link><pubDate>{date}</pubDate></item></channel></rss>'.encode()

class RailNoticeTests(unittest.TestCase):
    def test_candidates_preserve_time_and_unknown_location(self):
        events, source = parse_rail_notices(feed(), NOW)
        self.assertEqual(source['status'], 'ok')
        self.assertEqual(events[0]['observed_at'], '2026-10-24T23:00:00Z')
        self.assertIsNone(events[0]['near_corridor'])
        self.assertIsNone(events[0]['lat'])
        self.assertIn('candidate', events[0]['match_basis'])

    def test_stale_news_cannot_be_current(self):
        events, source = parse_rail_notices(feed('Tue, 29 Sep 2026 05:53:31 +0000'), NOW)
        self.assertEqual(source['status'], 'stale')
        self.assertNotEqual(source['generated_at'], source['fetched_at'])
        self.assertEqual(len(events), 1)

    def test_bad_links_dates_payload_and_failure(self):
        events, source = parse_rail_notices(feed(link='https://evil.example/news'), NOW)
        self.assertEqual(events, [])
        self.assertEqual(source['rejected_count'], 1)
        self.assertRaises(ValueError, parse_rail_notices, b'x' * (MAX_BYTES + 1), NOW)
        self.assertRaises(ValueError, parse_rail_notices, b'<!DOCTYPE rss><rss/>', NOW)
        with patch('corridor_lifeline.rail_notices.urlopen', side_effect=TimeoutError()):
            events, sources = fetch_rail_notices(NOW)
        self.assertEqual(events, [])
        self.assertEqual(sources[0]['status'], 'error')
        self.assertIsNone(sources[0]['generated_at'])
