import copy
from datetime import timedelta
from email import policy
from email.parser import BytesParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError

from corridor_lifeline.adapters import collect, weather, warnings, rail, timestamp, read
from corridor_lifeline.engine import score
from corridor_lifeline.alerts import draft
from corridor_lifeline.__main__ import load_config, run_once, main

ROOT = Path(__file__).resolve().parents[1]


class LifelineTests(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / 'fixtures/2024'
        self.config = load_config(self.base / 'config.json')
        self.now = timestamp(self.config['as_of'])
        self.feeds = collect(self.config, self.base, self.now)

    def evaluate(self):
        return score(self.config, self.feeds, self.now)

    def test_closure_is_critical_and_capped(self):
        result = self.evaluate()
        self.assertEqual((result['score'], result['level']), (100, 'CRITICAL'))
        self.assertEqual(result['components'], {'rainfall':25, 'warnings':30, 'rail':100})

    def test_reopening_fixture(self):
        base = ROOT / 'fixtures/2022'
        config = load_config(base / 'config.json')
        now = timestamp(config['as_of'])
        result = score(config, collect(config, base, now), now)
        self.assertEqual((result['score'], result['rail_status']), (0, 'open'))

    def test_rain_thresholds(self):
        self.feeds[1]['data']['items'] = []
        self.feeds[2]['data']['status'] = 'open'
        for rain, expected in [(0,0),(24.9,0),(25,10),(49.9,10),(50,25),(99.9,25),(100,40)]:
            self.feeds[0]['data']['rain_since_9am_mm'] = rain
            self.assertEqual(self.evaluate()['score'], expected)

    def test_no_duplicate_station_or_warning_points(self):
        self.feeds += copy.deepcopy(self.feeds[:2])
        self.assertEqual(self.evaluate()['components']['warnings'], 30)
        self.assertEqual(self.evaluate()['components']['rainfall'], 25)

    def test_stale_data_never_low_or_current_closure(self):
        feeds = collect(self.config, self.base, self.now + timedelta(days=2))
        result = score(self.config, feeds, self.now + timedelta(days=2))
        self.assertEqual(result['level'], 'UNKNOWN')
        self.assertEqual(result['rail_status'], 'unknown')
        self.assertEqual(len(result['issues']), 3)

    def test_future_data_is_error(self):
        feeds = collect(self.config, self.base, self.now - timedelta(hours=1))
        self.assertTrue(all(f['health'] == 'error' for f in feeds))

    def test_one_failed_feed_preserves_closure(self):
        self.feeds[0].update(health='error', error='offline')
        self.assertEqual(self.evaluate()['level'], 'CRITICAL')
        self.assertEqual(self.evaluate()['coverage'], 'incomplete')

    def test_statewide_warning_is_not_assumed_corridor_match(self):
        self.feeds[1]['data']['items'][0].update(title='Severe Weather Warning', description='Perth')
        self.assertEqual(self.evaluate()['components']['warnings'], 10)

    def test_cancelled_warning_not_counted(self):
        self.feeds[1]['data']['items'][0]['title'] = 'Cancellation of Flood Warning for Rawlinna'
        self.assertEqual(self.evaluate()['components']['warnings'], 0)

    def test_weather_uses_latest_not_sum_since_9am(self):
        data = {'observations':{'data':[
            {'aifstime_utc':'20240327070000','rain_trace':'25'},
            {'aifstime_utc':'20240327080000','rain_trace':'50'}]}}
        self.assertEqual(weather(json.dumps(data), {'name':'Station'})['rain_since_9am_mm'], 50)
        for invalid in ['NaN', '-1', '-', None, 'Infinity']:
            data['observations']['data'][1]['rain_trace'] = invalid
            with self.assertRaises(ValueError):
                weather(json.dumps(data), {'name':'Station'})

    def test_bad_rss_and_missing_timestamp(self):
        for content in ['<html/>', '<rss><channel/></rss>']:
            with self.assertRaises(ValueError):
                warnings(content, {})

    def test_rail_validation(self):
        data = json.loads((self.base/'rail.json').read_text())
        for key, value in [('status','reopening soon'),('corridor_id','other'),('observed_at','2024-03-27T08:00:00')]:
            invalid = dict(data, **{key:value})
            with self.assertRaises(ValueError):
                rail(json.dumps(invalid), {'corridor_id':'east-west'})

    def test_missing_and_malformed_sources_are_visible(self):
        for data in [b'not json', b'{}']:
            with patch('corridor_lifeline.adapters.read', return_value=data):
                feeds = collect(self.config, self.base, self.now)
                self.assertTrue(all(f['health'] == 'error' for f in feeds))
        with patch('corridor_lifeline.adapters.read', side_effect=URLError('offline')):
            self.assertTrue(all(f['health']=='error' for f in collect(self.config,self.base,self.now)))

    def test_http_adapter_uses_timeout_and_bounded_read(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{}'
        with patch('corridor_lifeline.adapters.urlopen', return_value=response) as request:
            self.assertEqual(read('https://example.test/feed', self.base), b'{}')
            self.assertEqual(request.call_args.kwargs['timeout'],20)
            response.__enter__.return_value.read.assert_called_once_with(2_000_001)

    def test_email_has_plain_body_no_recipients_and_demo_label(self):
        plain, raw = draft(self.evaluate(), True)
        message = BytesParser(policy=policy.default).parsebytes(raw)
        self.assertIn('[DEMO]', message['Subject'])
        self.assertIsNone(message['To'])
        self.assertEqual(message.get_content_type(),'text/plain')
        self.assertIn('not a closure probability',message.get_content())
        self.assertIn('DEMO ONLY',plain)
        self.assertIn('https://www.artc.com.au/',plain)

    def test_outputs_and_cli_demo_offline(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            command = [sys.executable,'-m','corridor_lifeline','demo','--out',str(out)]
            result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(list(out.rglob('alert.eml'))),2)
            saved = json.loads((out/'demo/2024/latest.json').read_text())
            self.assertIn('fixture_note', saved)
            self.assertEqual(saved['score'],100)

    def test_scheduler_polls_again_after_source_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = ['lifeline','watch','--config',str(self.base/'config.json'),'--out',temporary,'--interval','60']
            with patch.object(sys,'argv',args), patch('corridor_lifeline.__main__.run_once', return_value={'issues':['offline']}) as poll, patch('corridor_lifeline.__main__.time.sleep',side_effect=[None,KeyboardInterrupt]):
                self.assertEqual(main(),0)
                self.assertEqual(poll.call_count,2)


if __name__ == '__main__':
    unittest.main()
