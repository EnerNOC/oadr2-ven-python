# For receiving and sending XMPP data

__author__ = 'Thom Nichols <tnichols@enernoc.com>, Benjamin N. Summerton <bsummerton@enernoc.com>'

import threading, time, logging, xdrlib, base64
from cStringIO import StringIO
from xml.sax.saxutils import escape as escape_xml
import lxml
from lxml import etree

import event, poll

import xml.etree.ElementTree
from xml.etree.cElementTree import XML

import sleekxmpp
from sleekxmpp.stanza.iq import Iq
from sleekxmpp.plugins.base import base_plugin
from sleekxmpp.exceptions import XMPPError


__XMPP_INSTANCE = None

# Make sure that we only get once instance of the poll thingy
def get_instance(**kwargs):
    global __XMPP_INSTANCE

    if __XMPP_INSTANCE is None:
        __XMPP_INSTANCE = OpenADR2(**kwargs)

    return __XMPP_INSTANCE
    

# Handler class/service for the XMPP stuff
class OpenADR2(poll.OpenADR2):
    # Memeber variables
    # --------
    # Everything from poll.OpenADR2 class
    # xmpp_client - a sleekxmpp.ClientXMPP object, which will intercept the OpenADR2 stuff for us
    # _message_signal_match - an event listener for matching signals
    # user - JID
    # password - Password for accompanying JID
    # http_certs - 
    # server_addr - Address of the XMPP Server
    # server_port - Port we should connect to


    # Initilize what will do XMPP magic for us
    # **poll_config - A dictionary of Keyord arguemnts for the base class (poll.OpenADR2)
    # user - JID of whom we want to login to as on the XMPP Server
    # password - Password for corresponding JID
    # http_certs - For XEP-0066 plugin
    def __init__(self, poll_config, user, password, server_addr='localhost', server_port=5222, http_certs=None):
        self.xmpp_client = None
        self.user = user
        self.password = password
        self.server_addr = server_addr
        self.server_port = int(server_port)
        self.http_certs = http_certs

        poll.OpenADR2.__init__(self, **poll_config)

    # Setup/Start the client.
    # start_thread - To start the thread or to not
    def _init_client(self, start_thread):
        # Setup the XMPP Client that we are going to be using
        self.xmpp_client = sleekxmpp.ClientXMPP(self.user, self.password)
        self.xmpp_client.add_event_handler('session_start', self.xmpp_session_start)
        self.xmpp_client.add_event_handler('message', self.xmpp_message)
        self.xmpp_client.register_plugin('xep_0004')
        self.xmpp_client.register_plugin('xep_0030')
        self.xmpp_client.register_plugin('xep_0047')
        self.xmpp_client.register_plugin('xep_0066', pconfig={'ca_certs': self.http_certs})
        self.xmpp_client.register_plugin('xep_0060')
        self.xmpp_client.register_plugin('xep_0050')
        self.xmpp_client.register_plugin('xep_0199', pconfig={'keepalive': True, 'frequency': 240})
        self.xmpp_client.register_plugin('xep_0202')
        self.xmpp_client.register_plugin('OpenADR2Plugin', module='oadr2.xmpp',
                                         pconfig={'msg_handler': self._handle_payload_signal})
        # TODO: Add XEP-0096?

        # Setup system information disco
        self.xmpp_client['xep_0030'].add_identity(category='system', itype='version', name='OpenADR2 Python VEN')
        
        self.xmpp_client.connect((self.server_addr, self.server_port))
        self.xmpp_client.process(threaded=True)

    # 'session_start' event handler for our XMPP Client
    # event - An event.
    def xmpp_session_start(self, event):
        self.xmpp_client.getRoster()
        self.xmpp_client.sendPresence()

    # 'message' event handler for our XMPP Client
    # msg - The Message.
    def xmpp_message(self, msg):
        logging.info(msg)

    # Handle a message
    # msg - A type of OADR2Message
    def _handle_payload_signal(self,msg):
        if msg.type != 'OADR2':
            return

        # Try to generate a response payload and send it back
        try:
            logging.info('Signal (message) handler received a payload, processing...')
            response = self.event_handler.handle_payload( msg.payload )
            logging.info('Response Payload:\n%s\n----\n'%etree.tostring(response, pretty_print=True))
            self.send_reply( response, msg.from_ )
        except Exception, ex:
            logging.exception("Error processing OADR2 log request: %s", ex)

    
    # Make and OADR2 Message and sends it to someone (if they are online)
    # payload - The body of the IQ stanza, i.e. the OpenADR xml stuff (etree.Element object)
    # to - The JID of whom the messge will go to
    def send_reply( self, payload, to ):
        # Make the message
        iq = OADR2Message(
            payload = payload,
            iq_type = 'set'
        )

        # And send it if we are connected
        if self.xmpp_client.state.current_state() == 'connected':
            reply = Iq(self.xmpp_client, sto=to, stype=iq.iq_type)

            xml_items = []
            for i in iq.to_xml():
                xml_items.append(XML(i))

            reply.set_payload(xml_items)
            self.xmpp_client.send(reply)
        
    # Our poll_vtn_loop.
    # Overloading the one in the base class
    def poll_vtn_loop(self):
        logging.warn("An OADR 2.0 XMPP client should not be using the server" )
        logging.warn("it should be waiting for XMPP IQs to be pushed!" )


    # Shutdown the client
    def exit(self):
        # Shutdown the xmpp client
        logging.info('Shutting down the XMPP Client...')
        self.xmpp_client.send_presence(pstatus='unavailable')
        self.xmpp_client.disconnect()
        self.xmpp_client.stop.set()
        self.xmpp_client = None
        logging.info('XMPP Client shutdown.')

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

    # Get the message's payload as XML
    # Return: An XML String of the payload.  Does not include IQ tags
    def to_xml(self):
        data = []
        buffer = StringIO()
        if self.payload is not None: 
            buffer.write(etree.tostring(self.payload))
            data.append(buffer.getvalue())
        if self.error:
            data.append(self.error.to_xml())

        return data


# NOTE: This plugin only works in the space of OpenADR 2.0a, but it shouldn't be to hard to have it work with 2.0b as well
class OpenADR2Plugin(base_plugin):
    '''
    OpenADR 2.0 XMPP handler
    '''

    # Called when initialize the plugin, not the same as __init__
    def plugin_init(self):
        self.xep = 'OADR2'
        self.description = 'OpenADR 2.0 XMPP EiEvent Implementation'
        self.xmpp.add_handler("<iq type='set'><oadrDistributeEvent xmlns='%s' /></iq>"%event.OADR_XMLNS_A,
                              self._handle_iq)
        self.msg_handler = self.config.get('msg_handler')

    def _handle_iq(self, iq):
        logging.info('OpenADR2Plugin: recieved a valid IQ Stanza. -- from=%s, to=%s'%(iq.get('from'), iq.get('to')))
        try:
            # Convert a "Standard Python Library XML object," to one from lxml
            payload_element = lxml.etree.XML(xml.etree.ElementTree.tostring(iq[0]))
            msg = OADR2Message(
                iq_type = iq.get('type'),
                id_ = iq.get('id'), 
                from_ = iq.get('from'),
                payload = payload_element
            )
            
            # And pass it to the message handler
            self.msg_handler(msg)
        except Exception, e:
            logging.exception("OADR2 XMPP parse error: %s", e)
            raise XMPPError(text=e) 

