# Contains the EventController and ControlInterface classes

__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

import logging
import time
import threading
from oadr2 import event, schedule

CONTROL_LOOP_INTERVAL = 30           # update control state every X second

event_levels = ( 
    'relay_1A',    # 1+
    'relay_2A',    # 2+
)

# A sort of mock register/memory for the feedbacks and event levels
register = {
    'pulse_1': 0,       # (val, timestamp)
    'pulse_2': 0,       # (val, timestamp)
    'relay_1A': 0,
    'relay_2A': 0,
}


# Used by poll.OpenADR2 to handle events
class EventController(object):
    '''
    EventController is a class that is used to pass events to the EventHandler.

    Member Variables:
    --------
    event_handler -- The EventHandler instance
    current_signal_level -- current signal level of a realy/point
    control_loop_interval -- How often to run the control loop
    event_levels -- A variable that contains the current event levels
    _control_loop_signal -- threading.Event() object
    _control -- A ControlInterface instance
    _exit -- A threading.Thread() object
    '''


    def __init__(self, event_handler, control_loop_interval=CONTROL_LOOP_INTERVAL):
        '''
        Initialize the Event Controller

        event_handler -- An instance of event.EventHandler
        control_loop_interval -- How often to run the control loop
        '''

        # Set the control interface
        self._control = ControlInterface()

        self.event_handler = event_handler
        self.current_signal_level = 0 

        # Add an exit thread for the module
        self._exit = threading.Event()
        self._exit.clear()

        self._control_loop_signal = threading.Event()
        self.control_loop_interval = control_loop_interval

        global event_levels
        self.event_levels = event_levels


    def control_event_loop(self):
        '''
        This is the threading loop to perform control based on current oadr events
        Note the current implementation simply loops based on CONTROL_LOOP_INTERVAL
        except when an updated event is received by a VTN.
        '''

        self._exit.wait(10)  # give a couple seconds before performing first control

        try:
            self.current_signal_level = self.get_current_relay_level()

        except Exception, ex:
            logging.warn("Error reading initial hardware state! %s",ex)

        while not self._exit.is_set():
            try:
                logging.debug("Updating control states...")
                events = self.event_handler.get_active_events()
                self.do_control(events)

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
        remove_events = []
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

        self.event_handler.remove_events(remove_events)

        logging.debug("Highest signal level is: %f", highest_signal_val)
        
        self.toggle_relays(highest_signal_val)

    
    def toggle_relays(self, signal_level):
        '''
        Toggles the relays on the hardware (via the control interface).

        signal_level -- If it is the same as the current signal level, the
                        function will exit.  Else, it will change the
                        signal relay
        '''

        # Run a check
        signal_level = float(signal_level)
        if signal_level == self.current_signal_level:
            return

        for i in range(len(self.event_levels)):
            control_val = 1 if i < signal_level else 0
            self._control.do_control_point('control_set', self.event_levels[i], control_val)

        self.current_signal_level = signal_level


    def get_current_relay_level(self):
        '''
        Gets the current relay levels for us (from the control interface).

        Returns: '0' if all control points are at '0'.  Any non-Zero number
                  otherwise.
        '''

        for i in xrange(len(self.event_levels),0,-1):
             val = self._control.do_control_point('control_get', self.event_levels[i-1])
             if val:
                return i

        return 0


class ControlInterface(object):
    '''
    ControlInterface is a class that is used to interface with hardware that
    this code may run on.

    Member variables:
    _register -- A sorty of "memory," to store/get relay values.
    '''


    def __init__(self):
        '''
        Initialize the class.
        '''
        self._register = register.copy() # Use our own register for the control mock


    def do_control_point(self, op, point_id, value=None):
        '''
        Do an operation on a control point (e.g. get/set)

        op -- Either 'control_get' to get a value, or 'control_set' to set it.
        point_id -- What point to operate on
        value -- When setting, this is what to set the point to

        Returns: on a Get, it will return the value of the point requested
        '''

        if op == 'control_get':
            # Perform an 'Control Get' operation
            if point_id in self._register:
                return self._register[point_id], time.time()
            else:
                # We shoudn't be here
                logging.warn('In ControlInterface, tried to get point_id "%s," which doesn\'t exist in the register.'%(point_id))
                return None, None
        elif op == 'control_set':
            # Set something in the "register,"
            if (point_id in self._register) and (value is not None):
                self._register[point_id] = value
            else:
                if value is None:
                    logging.warn('In ControInterface, tried to set a None type value for register w/ point_id=%s.'%(point_id))
                    return None
                if point_id not in self._register:
                    logging.warn('In ControlInterface, tried to set pont_id "%s," which doesn\'t exist in the register.'%(point_id))
                    return None

