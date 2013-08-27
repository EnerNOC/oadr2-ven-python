
'''
This module handles scheduling for OpenADR2 entities, 
e.g. event schedules, price schedules, etc.
'''

__author__ = 'Thom Nichols tnichols@enernoc.com'

import re
import datetime
import random
#import logging

DB_PATH = 'oadr2.db'


DURATION_PAT = r'([+-])?P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
DURATION_REX = re.compile(DURATION_PAT)


def parse_duration(dur_str):
    '''
    Parse a duration string as defined by RFC-5545 xCal spec:
    http://tools.ietf.org/html/rfc5545#section-3.3.6

    Returns a tuple of `(sign,weeks,days,hours,minutes,seconds)`
    If any of the increments are omitted, the value for that 
    increment will be `0`.  If sign is omitted, it defaults to '+'

    Example:
    `parse_duration('P15DT5H20S')` -> `(None, None, '15', '5', None, '20')`
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
        dur_vals = parse_duration(dur_list[i])
        sign = dur_vals[0]
        delta = datetime.timedelta(
                weeks= dur_vals[1],
                days= dur_vals[2],
                hours= dur_vals[3],
                minutes= dur_vals[4],
                seconds= dur_vals[5] )

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
        if not start_before and not start_after:
            return dttm # no offset

        dur_vals = parse_duration(start_before if start_before else start_after)

        delta = datetime.timedelta(
                weeks= dur_vals[1],
                days= dur_vals[2],
                hours= dur_vals[3],
                minutes= dur_vals[4],
                seconds= dur_vals[5] )

        # TODO might be more correct to add this value to a dttm, then figure
        # the seconds difference between start & new val
        total_seconds = (delta.seconds + delta.days * 24 * 3600)
        random_offset = random.randint( 0, total_seconds)

        delta = datetime.timedelta(seconds=random_offset)

        return dttm - delta if start_before else dttm + delta

