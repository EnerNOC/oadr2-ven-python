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
                    target=self.control_event_loop)
            self.control_thread.daemon = True
            self.control_thread.start()


    def events_updated(self):
        '''
        Call this when some events have updated to cause the control
        loop to refresh
        '''
        self._control_loop_signal.set()


    def control_event_loop(self):
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

                new_signal_level = self.do_control(events)
                logging.debug("Highest signal level is: %f", new_signal_level)

                changed = self.set_signal_level(new_signal_level)
                if changed:
                    logging.debug("Updated current signal level!")

            except Exception as ex:
                logging.exception("Control loop error: %s", ex)

            self._control_loop_signal.wait(CONTROL_LOOP_INTERVAL)
            self._control_loop_signal.clear() # in case it was triggered by a poll update

        logging.info("Control loop exiting.")


    def do_control(self, events):
        '''
        Called by `control_event_loop()` when event states should be updated.
        This parses through the events, and toggles them if they are active. 

        events -- List of lxml.etree.ElementTree objects (with OpenADR 2.0 tags)
        '''
        highest_signal_val = 0
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
                highest_signal_val = max(signal_level, highest_signal_val)

            except Exception as e:
                logging.exception("Error parsing event: %s", e)

        # remove any events that we've detected have ended.
        # TODO callback for expired events??
        self.event_handler.remove_events(remove_events)
        
        return highest_signal_val

    
    def set_signal_level(self, signal_level):
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

