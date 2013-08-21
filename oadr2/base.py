# BaseHandler class - Acts a base object for poll.OpenADR2 and xmpp.OpenADR2

__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

import logging, threading
import event, control


class BaseHandler(object):
    '''
    This object acts as a base for poll.OpenADR2 and xmpp.OpenADR2.

    Member Variables:
    --------
    event_handler -- The single instance of the event_handler, gotten via event.get_instace()
    event_controller -- A control.EventController object.
    _exit -- A threading object via threading.Event()
    --------
    '''

    def __init__(self, event_config):
        '''
        Initizlie the Base

        event_config -- A dictionary containing key-word arugments for the
                        EventHandller
        '''

        # Get an EventHandler and an EventController
        self.event_handler = event.EventHandler(**event_config)
        self.event_controller = control.EventController(self.event_handler)

        # Add an exit thread for the module
        self._exit = threading.Event()
        self._exit.clear()

        logging.info('Created base handler.')


    def exit(self):
        '''
        Shutdown the base handler and its threads.
        '''

        self.event_controller.exit()    # Stop the event controller
        self._exit.set()

        logging.info('Shutdown base handler.')


