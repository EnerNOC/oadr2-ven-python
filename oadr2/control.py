__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com' 

import logging
import time

feedback_map = {
    'a' : '00000000/pulse_1',
    'b' : '00000000/pulse_2',
}

event_levels = ( 
    '00000000/relay_1A',    # 1+
    '00000000/relay_2A',    # 2+
)

# A sort of mock register/memory for the feedbacks and event levels
register = {
    '00000000/pulse_1': 0,       # (val, timestamp)
    '00000000/pulse_2': 0,       # (val, timestamp)
    '00000000/relay_1A': 0,
    '00000000/relay_2A': 0,
}

__CONTROL_INSTANCE = None

# We should only have once instance of the Control Interface in use
def get_instance():
    global __CONTROL_INSTANCE

    if __CONTROL_INSTANCE is None:
        __CONTROL_INSTANCE = ControlInterface()

    return __CONTROL_INSTANCE


# This class is a sort of interface to the hardware
class ControlInterface(object):
    def __init__(self):
        self._register = register.copy() # Use our own register for the control mock

    def do_control_point(self, op, point_id, value=None, callback=None):
        if op == 'control_get':
            
            # Perform an 'Control Get' operation
            if point_id in self._register:
                return self._register[point_id], time.time()
            else:
                # We shoudn't be here
                logging.warn('In ControlInterface, tried to get point_id "%s," which doesn\'t exist in the register.'%(point_id))
        elif op == 'control_set':
            # Set something in the "register,"
            if (point_id in self._register) and (value is not None):
                self._register[point_id] = value
            else:
                if value is None:
                    logging.warn('In ControInterface, tried to set a None type value for register w/ point_id=%s.'%(point_id))
                if point_id not in self._register:
                    logging.warn('In ControlInterface, tried to set pont_id "%s," which doesn\'t exist in the register.'%(point_id))


