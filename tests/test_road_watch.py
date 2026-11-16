from datetime import datetime, timedelta, timezone
import unittest

from corridor_lifeline.road_watch import assess


class RoadWatchTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026,11,9,4,15,tzinfo=timezone.utc)
        first = self.now.replace(minute=0)
        hours = [dict(time=(first+timedelta(hours=i)).isoformat(), rain_mm=0, wind_kmh=3)
                 for i in range(48)]
        self.hours = hours
        self.payload = dict(status='ok', fetched_at=self.now.isoformat(),
                            sites=[dict(name='Port Hedland',lon=118.6,lat=-20.31,hours=hours)])

    def test_crossings_group_only_consecutive_hours(self):
        self.hours[1]['rain_mm'] = 8
        self.hours[2]['wind_kmh'] = 60
        self.hours[4]['rain_mm'] = 5
        result = assess(self.payload,self.now)
        self.assertEqual(result['status'],'watch')
        first, second = result['windows']
        self.assertEqual(first['end'], self.hours[2]['time'])
        self.assertEqual(second['start'],self.hours[4]['time'])
        self.assertEqual(first['peak_wind_kmh'],60)
        self.assertEqual(len(first['reasons']),2)

    def test_missing_and_stale_are_unknown(self):
        self.hours[3]['rain_mm'] = None
        self.assertEqual(assess(self.payload,self.now)['unknown_hours'],1)
        self.hours[1]['rain_mm'] = 20
        self.assertEqual(assess(self.payload,self.now+timedelta(hours=2))['status'],'unknown')
        self.payload['sites'][0]['lon'] = 0
        self.assertEqual(assess(self.payload,self.now)['windows'],[])
