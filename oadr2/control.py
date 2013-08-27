__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

import logging
import time
import threading
from oadr2 import event, schedule

CONTROL_LOOP_INTERVAL = 30   # update control state every X second


# Used by poll.OpenADR2 to handle events
class EventController(object):
    '''
    EventController tracks active events and fires a callback when event levels have 
    changed.

    Member Variables:
    --------
    event_handler -- The EventHandler instance
    current_signal_level -- current signal level of a realy/point
    control_loop_interval -- How often to run the control loop
    control_thread -- threading.Thread() object w/ name of 'oadr2.control'
    _control_loop_signal -- threading.Event() object
    _exit -- A threading.Thread() object
    '''


    def __init__(self, event_handler, 
            signal_changed_callback = None,
            start_thread = True,
            control_loop_interval = CONTROL_LOOP_INTERVAL):
        '''
        Initialize the Event Controller

        event_handler -- An instance of event.EventHandler
        start_thread -- Start the control thread
        control_loop_interval -- How often to run the control loop
        '''

        self.event_handler = event_handler
        self.current_signal_level = 0 

        self.signal_changed_callback = signal_changed_callback \
                if signal_changed_callback is not None \
                else self.default_signal_callback

        # Add an exit thread for the module
        self._exit = threading.Event()
        self._exit.clear()

        self._control_loop_signal = threading.Event()
        self.control_loop_interval = control_loop_interval

        # The control thread
        self.control_thread = None

        if start_thread:
            self.control_thread = threading.Thread(
                    name='oadr2.control',
                    target=self._control_event_loop)
            self.control_thread.daemon = True
            self.control_thread.start()


    def events_updated(self):
        '''
        Call this when some events have updated to cause the control
        loop to refresh
        '''
        self._control_loop_signal.set()


    def get_current_signal_level(self):
        '''
        Return the signal level and event ID of the currently active event.
        If no events are active, this will return (0,None)
        '''

        signal_level, event_id, expired_events = self._calculate_current_event_status(
                self.event_handler.get_active_events() )

        return signal_level, event_id


    def _control_event_loop(self):
        '''
        This is the threading loop to perform control based on current oadr events
        Note the current implementation simply loops based on CONTROL_LOOP_INTERVAL
        except when an updated event is received by a VTN.
        '''

        self._exit.wait(5)  # give a couple seconds before performing first control

        while not self._exit.is_set():
            try:
                logging.debug("Updating control states...")
                events = self.event_handler.get_active_events()

                new_signal_level = self._update_control(events)
                logging.debug("Highest signal level is: %f", new_signal_level)

                changed = self._update_signal_level(new_signal_level)
                if changed:
                    logging.debug("Updated current signal level!")

            except Exception as ex:
                logging.exception("Control loop error: %s", ex)

            self._control_loop_signal.wait(CONTROL_LOOP_INTERVAL)
            self._control_loop_signal.clear() # in case it was triggered by a poll update

        logging.info("Control loop exiting.")

    
    def _update_control(self, events):
        '''
        Called by `control_event_loop()` to determine the current signal level.
        This also deletes any events from the database that have expired.

        events -- List of lxml.etree.ElementTree objects (with OpenADR 2.0 tags)
        '''
        signal_level, evt_id, remove_events = self._calculate_current_event_status(events)

        if remove_events:
            # remove any events that we've detected have ended.
            # TODO callback for expired events??
            logging.debug("Removing completed events: %s", remove_events)
            self.event_handler.remove_events(remove_events)
        
        return signal_level


    def _calculate_current_event_status(self, events):
        '''
        returns a 3-tuple of (current_signal_level, current_event_id, remove_events=[])
        '''

        highest_signal_val = 0
        current_event_id = None
        remove_events = []  # to collect expired events

        for e in events:
            try:
                e_id = event.get_event_id(e, self.event_handler.ns_map)
                e_mod_num = event.get_mod_number(e, self.event_handler.ns_map)
                e_status = event.get_status(e, self.event_handler.ns_map)

                if not self.event_handler.check_target_info(e):
                    logging.debug("Ignoring event %s - no target match", e_id)
                    continue

                event_start_dttm = event.get_active_period_start(e, self.event_handler.ns_map)
                signals = event.get_signals(e, self.event_handler.ns_map)

                if signals is None:
                    logging.debug("Ignoring event %s - no valid signals", e_id)
                    continue

                logging.debug("All signals: %r", signals)
                intervals = [s[0] for s in signals]
                current_interval = schedule.choose_interval( event_start_dttm, intervals )

                if current_interval is None:
                    logging.debug("Event %s(%d) has ended", e_id, e_mod_num)
                    remove_events.append(e_id)
                    continue

                if current_interval < 0:
                    logging.debug("Event %s(%d) has not started yet.", e_id, e_mod_num)
                    continue

                logging.debug('---------- chose interval %d', current_interval)
                _, interval_uid, signal_level = signals[current_interval]
#                signal_level = event.get_current_signal_value(e, self.event_handler.ns_map)

                logging.debug('Control loop: Evt ID: %s(%s); Interval: %s; Current Signal: %s',
                        e_id, e_mod_num, interval_uid, signal_level )
                
                signal_level = float(signal_level) if signal_level is not None else 0

                if signal_level > highest_signal_val:
                    highest_signal_val = signal_level
                    current_event_id = e_id

            except Exception as e:
                logging.exception("Error parsing event: %s", e)

        return highest_signal_val, current_event_id, remove_events
    
    
    def _update_signal_level(self, signal_level):
        '''
        Called once each control interval with the 'current' signal level.
        If the signal level has changed from `current_signal_level`, this 
        calls `self.signal_changed_callback(current_signal_level, new_signal_level)`
        and then sets `self.current_signal_level = new_signal_level`.

        signal_level -- If it is the same as the current signal level, the
                        function will exit.  Else, it will change the
                        signal relay

        returns True if the signal level has changed from the `current_signal_level`
            or False if the signal level has not changed.
        '''

        # check if the current signal level is different from the new signal level
        if signal_level == self.current_signal_level:
            return False

        try:
            self.signal_changed_callback(self.current_signal_level, signal_level)
        
        except Exception as ex:
            logging.exception("Error from callback! %s", ex)

        self.current_signal_level = signal_level
        return True


    def default_signal_callback(self, old_level, new_level):
        '''
        The default callback just logs a message.
        '''
        logging.debug("Signal level changed from %f to %f", 
                old_level, new_level )


    def exit(self):
        '''
        Shutdown the threads for the module
        '''
        self._exit.set()
        self._control_loop_signal.set()  # interrupt sleep
        self.control_thread.join(2)

