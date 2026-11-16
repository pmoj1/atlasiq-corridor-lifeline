import copy
import math
import unittest

from corridor_lifeline.locations import check_location, load_catalog


class LocationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()

    def test_waypoint_exact_match_does_not_imply_coverage(self):
        result = check_location(-30.75, 121.47)
        self.assertEqual(result['nearest_waypoint']['id'], 'kalgoorlie')
        self.assertEqual(result['nearest_waypoint']['distance_km'], 0)
        self.assertEqual(result['nearest_segment']['distance_km'], 0)
        self.assertTrue(result['within_screening_buffer'])
        for field in ['monitoring_coverage', 'rail_status', 'mine_connection']:
            self.assertEqual(result[field], 'not_assessed')

    def test_far_location_is_outside_not_safe(self):
        result = check_location(-33.87, 151.21)
        self.assertFalse(result['within_screening_buffer'])
        self.assertGreater(result['nearest_segment']['distance_km'], 1000)
        self.assertEqual(result['rail_status'], 'not_assessed')

    def test_invalid_coordinates(self):
        for lat, lon in [(91, 0), (-91, 0), (0, 181), (0, -181), (math.nan, 0), (0, math.inf), (True, 0), ('0', 0), (None, 0)]:
            with self.subTest(lat=lat, lon=lon), self.assertRaises(ValueError):
                check_location(lat, lon)
        check_location(90, 180)
        check_location(-90, -180)

    def test_spherical_segment_distance_and_endpoint_clamp(self):
        c = copy.deepcopy(self.catalog)
        c['points'] = [{'id': 'a', 'name': 'A', 'lat': 0, 'lon': 0}, {'id': 'b', 'name': 'B', 'lat': 0, 'lon': 2}]
        c['segments'] = [{'id': 'ab', 'from': 'a', 'to': 'b', 'name': 'A–B'}]
        self.assertEqual(check_location(0, 1, c)['nearest_segment']['distance_km'], 0)
        self.assertAlmostEqual(check_location(1, 1, c)['nearest_segment']['distance_km'], 111.20, places=2)
        self.assertAlmostEqual(check_location(0, 3, c)['nearest_segment']['distance_km'], 111.20, places=2)
        self.assertTrue(check_location(0.4, 1, c)['within_screening_buffer'])
        self.assertFalse(check_location(0.5, 1, c)['within_screening_buffer'])

    def test_dateline_segment(self):
        c = copy.deepcopy(self.catalog)
        c['points'] = [{'id': 'a', 'name': 'A', 'lat': 0, 'lon': 179}, {'id': 'b', 'name': 'B', 'lat': 0, 'lon': -179}]
        c['segments'] = [{'id': 'ab', 'from': 'a', 'to': 'b', 'name': 'A–B'}]
        self.assertEqual(check_location(0, 180, c)['nearest_segment']['distance_km'], 0)
        self.assertGreater(check_location(0, 0, c)['nearest_segment']['distance_km'], 19000)

    def test_bad_catalogs_are_rejected(self):
        bad = []
        c = copy.deepcopy(self.catalog); c['points'][1]['id'] = c['points'][0]['id']; bad.append(c)
        c = copy.deepcopy(self.catalog); c['segments'][0]['to'] = 'missing'; bad.append(c)
        c = copy.deepcopy(self.catalog); c['points'][0]['lat'] = math.inf; bad.append(c)
        c = copy.deepcopy(self.catalog); c['screening_buffer_km'] = -1; bad.append(c)
        c = copy.deepcopy(self.catalog); c['geometry_kind'] = 'surveyed'; bad.append(c)
        for c in bad:
            with self.assertRaises(ValueError):
                check_location(0, 0, c)

    def test_results_do_not_mutate_catalog(self):
        original = copy.deepcopy(self.catalog)
        r = check_location(-30.75, 121.47, self.catalog)
        r['nearest_waypoint']['name'] = 'changed'
        r['nearest_segment']['name'] = 'changed'
        self.assertEqual(self.catalog, original)
