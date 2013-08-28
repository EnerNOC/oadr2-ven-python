
'''
This module handles scheduling for OpenADR2 entities, 
e.g. event schedules, price schedules, etc.
'''

__author__ = 'Thom Nichols tnichols@enernoc.com'

import re
import datetime
import calendar
import random
#import logging
from dateutil.relativedelta import relativedelta

DB_PATH = 'oadr2.db'


DURATION_PAT = r'([+-])?P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
DURATION_REX = re.compile(DURATION_PAT)


def parse_duration(dur_str):
    '''
    Parse a duration string as defined by ISO-8601:
    http://en.wikipedia.org/wiki/ISO_8601#Durations

    Returns a tuple of `(sign,years,months,days,hours,minutes,seconds)`
    If any of the increments are omitted, the value for that 
    increment will be `0`.  If sign is omitted, it defaults to '+'

    Example:
    `parse_duration('P15DT5H20S')` -> `('+', 0, 0, 15, 5, 0, 20)`
    '''
    groups = DURATION_REX.match(dur_str).groups()
    vals = tuple(int(i) if i is not None else 0 for i in groups[1:])
    return (groups[0] or '+',) + vals


def choose_interval(start,interval_list,now=None):
    '''
    Given a list of durations, find the duration that 'now' falls into.
    The returned value is the index of the `dur_list` or `None` if 
    the last interval still ends at some point before 'now'.
    The return value will be -1 if the event has not started yet.
    '''
    if now is None: now = datetime.datetime.utcnow()
    total_time = 0

    interval_start_list = durations_to_dates(
            start, interval_list )
#    logging.debug('All interval starts: %r', interval_start_list)

    current_interval_end = None
        
    for i in range(len(interval_start_list)):

        new_interval_end = interval_start_list[i]

        if new_interval_end > now: 
            # if the new interval is > now, we are in the interval prior.  
            # But if the prior interval is index 0, it means the event hasn't
            # started yet, in which case return value will = -1
            return i - 1

        if new_interval_end == current_interval_end:
            # means there was a 0 duration, which is a special case meaning 
            # 'unending' - this interval will always include 'now'
            return i - 1

        # else look at next interval: 
        current_interval_end = new_interval_end

    # the last interval still did not reach 'now',
    # which probably means the event has ended.
    return None


def duration_to_delta(duration_str):
    '''
    Take a duration string like 'PT5M' or 'P0Y0M1DT3H2M1S'
    and convert it to a dateutil relativedelta

    Returns - a 2-tuple containing (delta, sign) where sign is 
              either '+' or '-'
    '''
    vals = parse_duration( duration_str )
    sign = vals[0]
    return relativedelta(
                years= vals[1],
                months= vals[2],
                days= vals[3],
                hours= vals[4],
                minutes= vals[5],
                seconds= vals[6] ), sign


def durations_to_dates(start,dur_list):
    '''
    Return a date which is the designated amount of time
    from the given start datetime.
    @param `start` a datetime.datetime instance when the event should start
    @param `dur_list` a list of ical duration strings like `PT1M`
    @return a datetime which represents the start with the given duration offset
    '''
    if not isinstance(start,datetime.datetime):
        raise ValueError('start must be a datetime object')

    new_dttm = start
    new_list = [start,]

    for i in xrange(len(dur_list)):
        delta, sign = duration_to_delta( dur_list[i] )
        new_dttm = new_dttm + delta if sign == '+' else new_dttm - delta
        new_list.append( new_dttm )

    return new_list


def str_to_datetime(dt_str):
    fmt = '%Y-%m-%dT%H:%M:%S.%fZ' if '.' in dt_str \
            else '%Y-%m-%dT%H:%M:%SZ'
    return datetime.datetime.strptime(dt_str,fmt)


def dttm_to_str(dttm, include_msec=True):
    fmt = '%Y-%m-%dT%H:%M:%S.%fZ' if include_msec \
            else '%Y-%m-%dT%H:%M:%SZ'
    return dttm.strftime(fmt)


def random_offset(dttm, start_before, start_after):
    '''
    Given a start datetime, and a start_before and start_after duration,
    pick a random start time for this event.
    '''
    if not start_before and not start_after:
        return dttm # no offset

    min_dttm = dttm - duration_to_delta(start_before)[0] \
            if start_before else dttm

    max_dttm = dttm + duration_to_delta(start_after)[0] \
            if start_after else dttm

    timestamp1 = int(calendar.timegm(min_dttm.utctimetuple()))
    timestamp2 = int(calendar.timegm(max_dttm.utctimetuple()))

    random_start = random.randint(timestamp1, timestamp2)

    return datetime.datetime.utcfromtimestamp(random_start)

