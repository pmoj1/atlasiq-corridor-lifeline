import unittest
from corridor_lifeline.context import screen_mapped_notices


class MappedNoticeTests(unittest.TestCase):
    def test_freight_terminal_and_unlocated_notice(self):
        notices = [
            {'lon': 115.99, 'lat': -31.97, 'near_corridor': False},
            {'lat': None, 'lon': None, 'near_corridor': None},
        ]
        screen_mapped_notices(notices)
        self.assertTrue(notices[0]['near_corridor'])
        self.assertLess(notices[0]['distance_km'], 15)
        self.assertIn('mapped_section', notices[0])
        self.assertIsNone(notices[1]['near_corridor'])
        self.assertNotIn('distance_km', notices[1])
