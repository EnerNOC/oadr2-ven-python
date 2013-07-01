# For receiving and sending XMPP data

__author__ = 'Thom Nichols <tnichols@enernoc.com>, Benjamin N. Summerton <bsummerton@enernoc.com>'

import threading, time, logging, xdrlib, base64
from cStringIO import StringIO
from xml.sax.saxutils import escape as escape_xml
from lxml import etree

import event, poll

import xml.etree.ElementTree
from sleekxmpp.exceptions import XMPPError

# Handler class/service for the XMPP stuff
class OpenADR2(poll.OpenADR2):
    # Memeber variables
    # --------
    # Everything from poll.OpenADR2 class
    # _message_signal_match - an event listener for matching signals


    def __init__(self,*args,**kwargs):
        poll.OpenADR2.__init__(self, *args, **kwargs)


    # Setup/Start the client.
    # NOTE: the base class has a funciton of the same name, though it is never called
    # start_thread - To start the thread or to not
    def _init_client(self, start_thread):
        self._message_signal_match = events.add_event_listener(
                self._handle_payload_signal, 
                'alvin\'s hot juicebox', 
                'message_signal')

    # Handle a message
    # msg - A type of OADR2Message
    def _handle_payload_signal(self,msg):
        if msg.type != 'OADR2': return
        try:
#            logging.debug('---------- MSG payload: %s',msg.payload.tag)
#            logging.debug('---------- MSG child: %s',msg.payload[0].tag)
#            logging.debug('---------- MSG children: %s',msg.get_events())
           
#            print('Payload:')
#            print(etree.tostring(msg.payload, pretty_print=True))
#            print('----\n')
            response = self.event_handler.handle_payload( msg.payload )
#            print('Response:')
#            print(etree.tostring(response, pretty_print=True))
#            print('----\n')
            self.send_reply( response, msg.from_ )
        except Exception, ex:
            logging.exception("Error processing OADR2 log request: %s", ex)

    
    # Make and OADR2 Message and sends it to someone (if they are online)
    # payload - The body of the IQ stanza, i.e. the OpenADR xml stuff (etree.Element object)
    # to - The JID of whom the messge will go to
    def send_reply( self, payload, to ):
        # ack the IQ
        iq = OADR2Message(
            payload = payload,
            iq_type = 'set' )

        # TODO: have the client send a response
        
    # Our poll_vtn_loop.
    # Overloading the one in the base class
    def poll_vtn_loop(self):
        logging.warn("An OADR 2.0 XMPP client should not be using the server" )
        logging.warn("it should be waiting for XMPP IQs to be pushed!" )


    # Shutdown the client
    def exit(self):
        poll.OpenADR2.exit(self)        # Stop the parent class as well

class OADR2Message(object):
    '''Message for OADR2 payload'''

    def __init__(self, payload=None, 
            id_=None, stanza_type='iq', iq_type='result', 
            from_=None, to=None, error=None, type_='OADR2', 
            oadr_profile_level=event.OADR_PROFILE_20A):

        self.payload = payload
        self.id = id_
        self.from_ = from_
        self.type = type_
        self.stanza_type = stanza_type
        self.iq_type = iq_type
        self.error= error
        self.oadr_profile_level = oadr_profile_level
        
        # Set the namespace dependant upon the profile level
        if self.oadr_profile_level == event.OADR_PROFILE_20A:
            self.ns_map = event.NS_A
        elif self.oadr_profile_level == event.OADR_PROFILE_20B:
            self.ns_map = event.NS_B
        else:
            self.oadr_profile_level = OADR_PROFILE_20A     # Default/Safety, make it the 2.0a spec 
            self.ns_map = event.NS_A      

        Message.__init__(self)


    def get_events(self):
        return self.payload.findall("%{(oadr)s}oadrEvent/{%(ei)s}eiEvent"%self.ns_map)

    def get_status(self,event):
        return event.findtext("{%(ei)s}eventDescriptor/{%(ei)s}eventStatus"%self.ns_map)

    def get_evt_id(self,event):
        return event.findtext("{%(ei)s}eventDescriptor/{%(ei)s}eventID"%self.ns_map)

    def get_mod_num(self,event):
        return event.findtext("{%(ei)s}eventDescriptor/{%(ei)s}modificationNumber"%self.ns_map)

    def get_current_signal_level(self,event):
        return event.findtext(('{%(ei)s}eiEventSignals/{%(ei)s}eiEventSignal/' + \
                '{%(ei)s}currentValue/{%(ei)s}payloadFloat/{%(ei)s}value')%self.ns_map)

    def to_xml(self):
        data = []
        buffer = StringIO()
        if self.payload is not None: 
            buffer.write(etree.tostring(self.payload))
            data.append(buffer.getvalue())
        if self.error:
            data.append(self.error.to_xml())

        return data



service_class = OpenADR2

