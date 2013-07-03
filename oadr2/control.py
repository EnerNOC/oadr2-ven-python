# Contains the EventController and ControlInterface classes

__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

import logging
import time

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
    def __init__(self):
        pass


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

