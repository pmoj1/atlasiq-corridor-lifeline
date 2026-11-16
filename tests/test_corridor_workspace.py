import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from corridor_lifeline.history import record, recent
from corridor_lifeline.workspace import Workspace
from corridor_lifeline.dashboard import make_handler, render

ROOT = Path(__file__).resolve().parents[1]

class WorkspaceTests(unittest.TestCase):
    def test_history_dedup_retention(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'history.sqlite3'
            self.assertEqual(recent(path), [])
            record(path, {'score': 1}, limit=2)
            record(path, {'score': 1}, limit=2)
            self.assertEqual(len(recent(path)), 1)
            record(path, {'score': 2}, limit=2)
            record(path, {'score': 3}, limit=2)
            self.assertEqual(recent(path), [{'score': 3}, {'score': 2}])

    def test_worker_failure_and_single_flight(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Workspace(Path(folder) / 'missing.json', folder)
            entered, release = threading.Event(), threading.Event()
            def fail(*args):
                entered.set(); release.wait(3); raise ValueError('bad config')
            with patch('corridor_lifeline.workspace.load_config', side_effect=fail):
                self.assertTrue(workspace.start()); self.assertTrue(entered.wait(2))
                self.assertFalse(workspace.start()); release.set()
                import time
                for _ in range(100):
                    if not workspace.status()['running']: break
                    time.sleep(.01)
            self.assertEqual(workspace.status()['error'], 'bad config')

    def test_json_roundtrip_and_empty_workspace(self):
        data = json.loads((ROOT / 'output/demo/2024/latest.json').read_text())
        data['reasons'] = ['<script>literal</script>']
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'latest.json'; path.write_text(json.dumps(data))
            html = render(path)
            payload = html.split('id="saved-result">')[1].split('</script>')[0]
            self.assertEqual(json.loads(payload), data)
            html = render(Path(folder) / 'missing')
            self.assertIn('id="locations"', html)
            self.assertIn('Result unavailable', html)

    def test_http_checks_and_collection_authorization(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Workspace(ROOT / 'config/live.json', folder)
            handler = make_handler(Path(folder) / 'latest.json', 60, workspace, 'test-token')
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
            worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                result = json.load(urlopen(base + '/api/location-check?lat=-30.75&lon=121.47'))
                self.assertTrue(result['within_screening_buffer'])
                for suffix in ('lat=nan&lon=121', 'lat=91&lon=0', 'lat=0&lat=1&lon=2'):
                    with self.assertRaises(HTTPError) as error: urlopen(base + '/api/location-check?' + suffix)
                    self.assertEqual(error.exception.code, 400)
                with self.assertRaises(HTTPError) as error: urlopen(Request(base + '/api/collect', method='POST'))
                self.assertEqual(error.exception.code, 403)
                with patch.object(workspace, 'start', return_value=True) as start:
                    response = urlopen(Request(base + '/api/collect', method='POST', headers={'Origin': base, 'X-AtlasIQ-Token': 'test-token'}))
                    self.assertEqual(response.status, 202); start.assert_called_once()
            finally:
                server.shutdown(); server.server_close(); worker.join()
