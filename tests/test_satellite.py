import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from corridor_lifeline.satellite import parse_frames, satellite


class SatelliteTests(unittest.TestCase):
    def test_sorted_observations_only(self):
        now = datetime(2026, 11, 9, 1, tzinfo=timezone.utc)
        stamps = ["20261109004000", "20261109003000", "20261109100000", "bad"]
        records = [{"basetime": s, "validtime": s} for s in stamps]
        frames = parse_frames(records, now)
        self.assertEqual(len(frames), 1)
        self.assertIn("00:40:", frames[-1]["observed_at"])
        self.assertEqual(len(frames[-1]["tiles"]), 20)
        self.assertTrue(frames[-1]["tiles"][0].endswith("/5/26/16.jpg"))

    @patch("corridor_lifeline.satellite.urlopen", side_effect=TimeoutError)
    def test_catalogue_failure(self, _):
        result = satellite()
        self.assertEqual((result["status"], result["frames"]), ("unavailable", []))
