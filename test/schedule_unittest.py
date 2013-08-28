import sys,os
sys.path.insert( 0, os.getcwd() )

from oadr2 import schedule
import unittest
import datetime as dt
from dateutil.relativedelta import relativedelta

class ScheduleTest(unittest.TestCase):

    def test_parse_duration(self):

        self.assertEqual( ('+',0,0,0,0,3,0), schedule.parse_duration('PT3M') )
        self.assertEqual( ('+',0,0,0,0,3,0), schedule.parse_duration('+PT3M') )
        self.assertEqual( ('+',1,0,0,0,3,0), schedule.parse_duration('+P1YT3M') )
        self.assertEqual( ('+',0,0,0,0,3,0), schedule.parse_duration('P0YT3M') )
        self.assertEqual( ('+',0,0,0,0,0,30), schedule.parse_duration('P0Y0M0DT0H0M30S') )
        self.assertEqual( ('+',0,0,12,5,15,23), schedule.parse_duration('P12DT5H15M23S') )
        self.assertEqual( ('-',0,0,0,2,0,0), schedule.parse_duration('-PT2H') )
        self.assertEqual( ('+',0,0,12,0,0,0), schedule.parse_duration('P12D') )


    def test_parse_duration_to_delta(self):

        self.assertEqual( 
                (relativedelta(minutes=3),'+'), 
                schedule.duration_to_delta('PT3M') )

        self.assertEqual( 
                (relativedelta(minutes=3),'+'), 
                schedule.duration_to_delta('+PT3M') )

        self.assertEqual( 
                (relativedelta(years=1, minutes=5), '+'),
                schedule.duration_to_delta('+P1YT5M') )

        self.assertEqual( 
                (relativedelta(seconds=55), '+'),
                schedule.duration_to_delta('P0YT55S') )

        self.assertEqual( 
                (relativedelta(seconds=30), '+'),
                schedule.duration_to_delta('P0Y0M0DT0H0M30S') )

        self.assertEqual( 
                (relativedelta(days=12, hours=5, minutes=15, seconds=23), '+'),
                schedule.duration_to_delta('P12DT5H15M23S') )

        self.assertEqual( 
                (relativedelta(hours=2), '-'),
                schedule.duration_to_delta('-PT2H') )

        self.assertEqual( 
                (relativedelta(days=12), '+'),
                schedule.duration_to_delta('P12D') )


    def test_str_to_dttm(self):

        self.assertEqual(
                dt.datetime(2013,5,12,8,33,50),
                schedule.str_to_datetime('2013-05-12T08:33:50Z') )


    def test_dttm_to_str(self):

        self.assertEqual( '2013-05-12T08:33:50Z',
                schedule.dttm_to_str(dt.datetime(2013,5,12,8,33,50), include_msec=False) )


    def test_random_offset(self):

        start = dt.datetime(2013,5,12,8,33,50)

        dttm = schedule.random_offset(
                start, None, None )

        self.assertEqual( start, dttm )

        dttm = schedule.random_offset(
                start, 'PT3M', None )

        print("new dttm: %s" % dttm)
        min_dttm = dt.datetime(2013,5,12,8,30,50)
        self.assertTrue( dttm >= min_dttm and dttm < start )

        dttm2 = schedule.random_offset(
                start, 'PT1H', 'PT3D12M' )

        print("new dttm: %s" % dttm2)
        self.assertNotEqual( dttm, dttm2 )

        min_dttm = dt.datetime(2013,5,12,7,33,50)
        max_dttm = dt.datetime(2013,5,15,7,45,50)
        self.assertTrue( dttm >= min_dttm and dttm < max_dttm )


    def test_choose_interval(self):

        start = dt.datetime(2013,5,12,8,30,50)
        intervals = ('PT5M','PT30S','PT12H')
        
        # before event start
        self.assertEqual(-1, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,8,22,0) ) )
        
        # first interval (5 minutes)
        self.assertEqual(0, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,8,30,50) ) )

        self.assertEqual(0, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,8,30,51) ) )

        # second interval (30 seconds)
        self.assertEqual(1, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,8,35,50) ) )

        self.assertEqual(1, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,8,36,19) ) )

        # third interval (12 hours)
        self.assertEqual(2, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,8,36,20) ) )

        self.assertEqual(2, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,20,36,19) ) )

        # after the last interval
        self.assertEqual(None, schedule.choose_interval(start, intervals, 
            dt.datetime(2013,5,12,20,36,20) ) )



if __name__ == '__main__':
    unittest.main()
