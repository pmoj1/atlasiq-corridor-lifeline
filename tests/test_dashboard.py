import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from corridor_lifeline.dashboard import render, age_label


class DashboardTests(unittest.TestCase):
    def test_age_policy(self):
        now = datetime(2026, 10, 23, tzinfo=timezone.utc)
        self.assertIn('STALE', age_label('2024-01-01T00:00:00Z', now, 60))
        self.assertIn('future', age_label('2027-01-01T00:00:00Z', now, 60))
        self.assertIn('UNKNOWN', age_label('2026-10-23', now, 60))
        self.assertIn('RECENT', age_label(now.isoformat(), now, 60))

    def test_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'latest.json'
            self.assertIn('Result unavailable', render(path))
            for content in ('{', '[]', '{"score":0}'):
                path.write_text(content)
                self.assertIn('Result unavailable', render(path))

    def test_demo_and_escaping(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'output/demo/2024/latest.json').read_text())
        data['reasons'].append('<script>alert(1)</script>')
        data['issues'] = ['Missing weather']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'latest.json'
            path.write_text(json.dumps(data))
            html = render(path)
        self.assertIn('HISTORICAL DEMO', html)
        self.assertIn('Observed / verified at', html)
        self.assertIn('Fetched at', html)
        self.assertIn('Health at assessment', html)
        self.assertNotIn('<details open>', html)
        self.assertIn('STALE', html)
        self.assertIn('Missing weather', html)
        self.assertIn('100/100', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)
