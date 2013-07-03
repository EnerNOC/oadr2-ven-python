# Event Handler class.
# --------
# Requires the python libXML wrapper "lxml" to function properly

__author__ = "Thom Nichols <tnichols@enernoc.com>, Ben Summerton <bsummerton@enernoc.com>"

import uuid
import logging

from lxml import etree
from lxml.builder import ElementMaker, E

import schedule

'''
Code to manage eiEvents, parse schedules and current values.
'''

# Stuff for the 2.0a spec of OpenADR
OADR_XMLNS_A = 'http://openadr.org/oadr-2.0a/2012/07'
PYLD_XMLNS_A = 'http://docs.oasis-open.org/ns/energyinterop/201110/payloads'
EI_XMLNS_A   = 'http://docs.oasis-open.org/ns/energyinterop/201110'
EMIX_XMLNS_A = 'http://docs.oasis-open.org/ns/emix/2011/06'
XCAL_XMLNS_A = 'urn:ietf:params:xml:ns:icalendar-2.0'
STRM_XMLNS_A = 'urn:ietf:params:xml:ns:icalendar-2.0:stream'
NS_A = {
    'oadr' : OADR_XMLNS_A,
    'pyld' : PYLD_XMLNS_A,
    'ei'   : EI_XMLNS_A,
    'emix' : EMIX_XMLNS_A,
    'xcal' : XCAL_XMLNS_A,
    'strm' : STRM_XMLNS_A
}

# Stuff for the 2.0b spec of OpenADR
OADR_XMLNS_B          = "http://openadr.org/oadr-2.0b/2012/07"
DSIG11_XMLNS_B        = "http://www.w3.org/2009/xmldsig11#"
DS_XMLNS_B            = "http://www.w3.org/2000/09/xmldsig#"
CLM5ISO42173A_XMLNS_B = "urn:un:unece:uncefact:codelist:standard:5:ISO42173A:2010-04-07"
SCALE_XMLNS_B         = "http://docs.oasis-open.org/ns/emix/2011/06/siscale"
POWER_XMLNS_B         = "http://docs.oasis-open.org/ns/emix/2011/06/power"
GB_XMLNS_B            = "http://naesb.org/espi"
ATOM_XMLNS_B          = "http://www.w3.org/2005/Atom"
CCTS_XMLNS_B          = "urn:un:unece:uncefact:documentation:standard:CoreComponentsTechnicalSpecification:2"
GML_XMLNS_B           = "http://www.opengis.net/gml/3.2"
GMLSF_XMLNS_B         = "http://www.opengis.net/gmlsf/2.0"
NS_B = {    # If you see an 2.0a variable used here, that means that the namespace is the same
    'oadr'   : OADR_XMLNS_B,
    'pyld'   : PYLD_XMLNS_A,
    'ei'     : EI_XMLNS_A,
    'emix'   : EMIX_XMLNS_A,
    'xcal'   : XCAL_XMLNS_A,
    'strm'   : STRM_XMLNS_A,
    'dsig11' : DSIG11_XMLNS_B,
    'ds'     : DS_XMLNS_B,
    'clm'    : CLM5ISO42173A_XMLNS_B,
    'scale'  : SCALE_XMLNS_B,
    'power'  : POWER_XMLNS_B,
    'gb'     : GB_XMLNS_B,
    'atom'   : ATOM_XMLNS_B,
    'ccts'   : CCTS_XMLNS_B,
    'gml'    : GML_XMLNS_B,
    'gmlsf'  : GMLSF_XMLNS_B
}

# Other important constants that we need
VALID_SIGNAL_TYPES = ('level','price','delta','setpoint')
OADR_PROFILE_20A = '2.0a'
OADR_PROFILE_20B = '2.0b'

__EVENT_INSTANCE = None

# Make sure that we only use one instance of th Event Handler
# **kwargs - dictionary of keywored arugments
# Returns: Single instance of EventHandler
def get_instance(**kwargs):
    global __EVENT_INSTANCE

    if __EVENT_INSTANCE is None:
        __EVENT_INSTANCE = EventHandler(**kwargs)

    return __EVENT_INSTANCE


class EventHandler(object):
    # Our member variables:
    # --------
    # ven_id - This VEN's id
    # vtn_ids - List of ids of VTNs
    # oadr_profile_level - The profile level we have
    # ns_map - The XML namespace map we are using
    # market_contexts - List of Market Contexts
    # group_id - ID of group that VEN belogns to
    # resource_id - ID of resource in VEN we want to manipulate
    # party_id -
    # _events - Dictionary of events; KEY=ei:eventID, VALUE=etree.Element
    
    # Class constructor
    # vtn_ids - CSV string of VTN Ids we pat attention to
    # market_contexts - Another CSV string
    # group_id - Which group we belong to
    # resource_id - What resouce we are
    # party_id - Which party are we party of
    # ven_id - What is the ID of our unit
    def __init__(self, vtn_ids=None, market_contexts=None, group_id=None,
                 resource_id=None, party_id=None, ven_id=None,
                 oadr_profile_level=OADR_PROFILE_20A):
        # 'vtn_ids' is a CSV string of 
        self.vtn_ids = vtn_ids
        if self.vtn_ids is not None:
            self.vtn_ids = self.vtn_ids.split(',')

        # 'market_contexts' is also a CSV string
        self.market_contexts = market_contexts
        if self.market_contexts is not None: 
            self.market_contexts = self.market_contexts.split(',')

        self.group_id = group_id
        self.resource_id = resource_id
        self.party_id = party_id

        self.ven_id = ven_id

        # the default profile is '2.0a'; do this to set the ns_map
        self.oadr_profile_level = oadr_profile_level
        if self.oadr_profile_level == OADR_PROFILE_20A:
            self.ns_map = NS_A
        elif self.oadr_profile_level == OADR_PROFILE_20B:
            self.ns_map = NS_B
        else:
            self.oadr_profile_level = OADR_PROFILE_20A     # Default/Safety, make it the 2.0a spec 
            self.ns_map = NS_A      

        self._events = {}

    # Handle a payload
    # payload - An etree.Element object of oadr:oadrDistributeEvent as root node
    # Returns: An etree.Element object; which should be used as a response payload
    def handle_payload(self, payload):
        reply_events = []
        all_events = []

        requestID = payload.findtext('pyld:requestID',namespaces=self.ns_map)
        vtnID = payload.findtext('ei:vtnID',namespaces=self.ns_map)

        # If we got a payload from an VTN that is not in our list, send it a 400 message and return
        if self.vtn_ids and (vtnID not in self.vtn_ids):
            logging.warn("Unexpected VTN ID: %s, expected one of %r", vtnID, self.vtn_ids)
            return self.build_error_response( requestID, '400', 'Unknown vtnID: %s'% vtnID )

        # Loop through all of the oadr:oadrEvent 's in the payload
        for evt in payload.iterfind('oadr:oadrEvent',namespaces=self.ns_map):
            response_required = evt.findtext("oadr:oadrResponseRequired",namespaces=self.ns_map)
            evt = evt.find('ei:eiEvent',namespaces=self.ns_map) # go to nested eiEvent
            e_id = get_event_id(evt, self.ns_map)
            e_mod_num = get_mod_number(evt, self.ns_map)
            e_status = get_status(evt, self.ns_map)
            e_market_context = get_market_context(evt, self.ns_map)
            current_signal_val = get_current_signal_value(evt, self.ns_map)

            logging.debug('------ EVENT ID: %s(%s); Status: %s; Current Signal: %s',
                    e_id, e_mod_num, e_status, current_signal_val)
            
            all_events.append(e_id)
            old_event = self.get_event(e_id)
            old_mod_num = None
            
            if old_event is not None:                                   # If there is an older event
                old_mod_num = get_mod_number(old_event, self.ns_map)    # get it's mod number

            # For the events we need to reply to, make our "opts," and check the status of the event
            if (old_event is None) or (e_mod_num > old_mod_num) or (response_required == 'always'):
                # By default, we optIn and have an "OK," status (200)
                opt = 'optIn'
                status = '200'

                if (old_event is not None) and (old_mod_num > e_mod_num):
                    logging.warn(
                            "Got a smaller modification number (%d < %d) for event %s",
                            e_mod_num, old_mod_num, e_id )
                    status = '403'
                    opt = 'optOut'
                    
                if not self.check_target_info(evt):
                    logging.info("Opting out of event %s - no target match",e_id)
                    status = '403'
                    opt = 'optOut'

                valid_signals = get_signals(evt, self.ns_map)
                if valid_signals is None:
                    logging.info("Opting out of event %s - no simple signal",e_id)
                    opt = 'optOut'
                    status = '403'

                if self.market_contexts and (e_market_context not in self.market_contexts):
                    logging.info("Opting out of event %s - market context %s does not match",
                            e_id, e_market_context )
                    opt = 'optOut'
                    status = '405'

                reply_events.append((e_id,e_mod_num,requestID,opt,status))

            # We have a new event or an updated old one
            if (old_event is None) or (e_mod_num > old_mod_num):
                start_offset = get_start_before_after(evt, self.ns_map)

                # if we got some start offests
                if start_offset[0] or start_offset[1]:
                    start = get_active_period_start(evt, self.ns_map)

                    new_start = schedule.random_offset( start, 
                            start_offset[0], start_offset[1] )

                    logging.debug( "Randomizing start time for %s(%d) - " + \
                            "startBefore/ startAfter: %r. New start time: %s", 
                            e_id, e_mod_num, start_offset, new_start )

                    set_active_period_start(evt, new_start, self.ns_map)
                
                # Add/update the event to our list
                self.update_event(e_id,evt)

        # Find implicitly cancelled events and get rid of them
        remove_events = []
        for e_id in self._events:
            if e_id not in all_events: 
                logging.debug('Removing cancelled event %s', e_id)
                remove_events.append(e_id)
        self.remove_events(remove_events)

        # If we have any in the replay_events list, build some payloads
        logging.debug("Replying for events %r", reply_events)
        reply = None
        if reply_events:
            reply = self.build_created_payload(reply_events)

        return reply

    # Assemble an XML payload to request an event from the VTN
    # Returns: An etree.Element object
    def build_request_payload(self):
        oadr = ElementMaker(namespace=self.ns_map['oadr'], nsmap=self.ns_map)
        pyld = ElementMaker(namespace=self.ns_map['pyld'], nsmap=self.ns_map)
        ei = ElementMaker(namespace=self.ns_map['ei'], nsmap=self.ns_map)
        emix = ElementMaker(namespace=self.ns_map['emix'], nsmap=self.ns_map)

        payload = oadr.oadrRequestEvent(
                pyld.eiRequestEvent(
                    pyld.requestID(str(uuid.uuid4())),
#                    emix.marketContext('http://enernoc.com'),
                    ei.venID(self.ven_id),
#                    ei.eventID('asdf'),
#                    pyld.eventFilter('all'),
                    pyld.replyLimit('99')
                )
        ) 

        logging.debug( "Request payload:\n%s", 
                etree.tostring(payload,pretty_print=True) )
        return payload

    # Assemble an XML payload to send out for events marked 'response required'
    # events - List of tuples with the following structure:
    #            (Event ID,
    #             Modification Number,
    #             Request ID,
    #             Opt,
    #             Status)
    # Returns: An XML Tree in a string
    def build_created_payload(self,events):
        # Setup the element makers
        oadr = ElementMaker(namespace=self.ns_map['oadr'], nsmap=self.ns_map)
        pyld = ElementMaker(namespace=self.ns_map['pyld'], nsmap=self.ns_map)
        ei = ElementMaker(namespace=self.ns_map['ei'], nsmap=self.ns_map)

        def responses(events):
            for e_id,mod_num,requestID,opt,status in events:
                yield ei.eventResponse(
                        ei.responseCode(str(status)),
                        pyld.requestID(requestID),
                        ei.qualifiedEventID(
                            ei.eventID(e_id),
                            ei.modificationNumber(str(mod_num)) ),
                        ei.optType(opt) )

        payload = oadr.oadrCreatedEvent(
                pyld.eiCreatedEvent(
                    ei.eiResponse(
                        ei.responseCode('200'),
                        pyld.requestID() ),
                    ei.eventResponses( *list(responses(events)) ),
                    ei.venID(self.ven_id) ) )

        logging.debug( "Created payload:\n%s", 
                etree.tostring(payload,pretty_print=True) )
        return payload


    # Assemble the XML for an error response payload
    # request_id - Request ID of offending payload
    # code - The HTTP Error Code Status we want to use
    # description - An extra note on what was not acceptable
    # Returns: An etree.Element object containing the payload
    def build_error_response(self,request_id,code,description=None):
        '''
        Send an error eiCreatedEvent payload.
        NOTE: request_id and description are not used.
        '''
        oadr = ElementMaker(namespace=self.ns_map['oadr'], nsmap=self.ns_map)
        pyld = ElementMaker(namespace=self.ns_map['pyld'], nsmap=self.ns_map)
        ei = ElementMaker(namespace=self.ns_map['ei'], nsmap=self.ns_map)

        payload = oadr.oadrCreatedEvent(
                pyld.eiCreatedEvent(
                    ei.eiResponse(
                        ei.responseCode(code),
                        pyld.requestID() ),
                    ei.venID(self.ven_id) ) )

#        response = ei.eiResponse (
#                       ei.responseCode(code),
#                        pyld.requestID(request_id)
#                    )

        # Incase description is set
#        if description is not None:
#            response.append(ei.responseDescription(description))

        # Make the payload
#        payload = oadr.oadrCreatedEvent(
#                pyld.eiCreatedEvent( response, ei.venID(self.ven_id )))


        logging.debug( "Error payload:\n%s", 
                etree.tostring(payload,pretty_print=True) )
        return payload

    # Checks to see if we haven been targeted by the event
    # If none of the IDs belowed, then we want to respong to any event that we are given`
    def check_target_info(self,evt):
        accept = True
        party_ids = get_party_ids(evt, self.ns_map)
        group_ids = get_group_ids(evt, self.ns_map)
        resource_ids = get_resource_ids(evt, self.ns_map)
        ven_ids = get_ven_ids(evt, self.ns_map)

        if party_ids or group_ids or resource_ids or ven_ids:
            accept = False

            if party_ids and self.party_id in party_ids:
                accept = True

            if group_ids and self.group_id in group_ids:
                accept = True

            if resource_ids and self.resource_id in resource_ids:
                accept = True

            if ven_ids and self.ven_id in ven_ids:
                accept = True

        return accept
    
    # Get an iterator of all the active events
    # Return: An iterator containing the values of our _events dictionary
    def get_active_events(self):
        '''
        for now this is just in-memory, should be in sqlite.
        '''
        return self._events.itervalues()


    # Clear out all of the current events and add/update some other ones in
    # event_dict - Dictionary of events we want to add/update.
    #                - Key should be the Event ID
    #                - Value should be the Event
    def update_all_events(self, event_dict):
        '''
        replace all events with this event dict, keyed by event ID
        '''
        self._events.clear()
        for e_id in event_dict.iterkeys():
            self._events[e_id] = event_dict[e_id]


    # Sets an older event of e_id to the newer one, or just add a new one
    # e_id - ID of the event we want to replace/add
    # event - the event we want to add in
    def update_event(self,e_id,event):
        '''
        keep state for known seen events.  For now it's just an in-memory dict 
        but eventually should be a sqlite table
        '''
        self._events[e_id]= event

    # Get an event w/ a specific id
    # e_id - ID of the event we want
    # Return: The event we want, or None
    def get_event(self,e_id):
        '''
        Get any current event for the given event ID.
        This should eventually pull from a sqlite table.
        event ID globally unique if the VEN is participating w/ multiple VTNs
        '''
        return self._events.get(e_id,None)


    # Remove a list of events from our internal member dictionary
    # event_id_list - List of Event IDs 
    def remove_events(self,evt_id_list):
        '''
        Remove events from the VENs event state
        '''
        for e_id in evt_id_list:
            del self._events[e_id]



# Gets the event id of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: an ei:eventID value
def get_event_id(evt, ns_map=NS_A):
    return evt.findtext("ei:eventDescriptor/ei:eventID",namespaces=ns_map)


# Gets the status of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: an ei:eventStatus value
def get_status(evt, ns_map=NS_A):
    return evt.findtext("ei:eventDescriptor/ei:eventStatus",namespaces=ns_map)

# Gets the mod number of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: an ei:modificationNumber value
def get_mod_number(evt, ns_map=NS_A):
    return int( evt.findtext(
        "ei:eventDescriptor/ei:modificationNumber",
        namespaces=ns_map) )

# Gets the market context of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: an emix:marketContext value
def get_market_context(evt, ns_map=NS_A):
    return evt.findtext("ei:eventDescriptor/ei:eiMarketContext/emix:marketContext",namespaces=ns_map)


# Gets the signal value of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: an ei:value value
def get_current_signal_value(evt, ns_map=NS_A):
    return evt.findtext(
        'ei:eiEventSignals/ei:eiEventSignal/ei:currentValue/' + \
        'ei:payloadFloat/ei:value', namespaces=ns_map)


# Gets the signals of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: A list of tuples of (xcal:duration, xcal:text, ei:value)
def get_signals(evt, ns_map=NS_A):
    '''
    return a list of tuples in the form (duration,uid,signalPayload_value)
    '''
    simple_signal = None
    signals = []
    for signal in evt.iterfind( 'ei:eiEventSignals/ei:eiEventSignal', namespaces=ns_map ):
        signal_name = signal.findtext('ei:signalName', namespaces=ns_map)
        signal_type = signal.findtext('ei:signalType', namespaces=ns_map)
        
        if signal_name == 'simple' and signal_type in VALID_SIGNAL_TYPES:
            simple_signal = signal  # This is A profile only conformance rule!

    if simple_signal is None: return None

    for interval in simple_signal.iterfind( 'strm:intervals/ei:interval', namespaces=ns_map ):
        duration = interval.findtext( 'xcal:duration/xcal:duration', namespaces=ns_map )
        uid = interval.findtext('xcal:uid/xcal:text', namespaces=ns_map)
        value = interval.findtext('ei:signalPayload//ei:value', namespaces=ns_map)
        signals.append( (duration,uid,value) )

    return signals


# Gets the active period start of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: a schedule'd datetime object
def get_active_period_start(evt, ns_map=NS_A):
    '''
    Get the activeperiod start as a datetime
    `event` must be an ei:eiEvent lxml.etree.Element
    '''
    dttm_str = evt.findtext(
            'ei:eiActivePeriod/xcal:properties/xcal:dtstart/xcal:date-time',
            namespaces=ns_map )
    return schedule.str_to_datetime(dttm_str)


# Sets the "active period start," of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
def set_active_period_start(evt,dttm, ns_map=NS_A):
    active_period_element = evt.find(
            'ei:eiActivePeriod/xcal:properties/xcal:dtstart/xcal:date-time',
            namespaces=ns_map )
    active_period_element.text = schedule.dttm_to_str(dttm)


# Gets the "start before after," of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: A tuple of (xcal:startbefore, xcal:startafter)
def get_start_before_after(evt, ns_map=NS_A):
    '''
    Get the startBefore/ startAfter elements.  May be (None,None)
    '''
    return ( evt.findtext(
            'ei:eiActivePeriod/xcal:properties/xcal:tolerance/xcal:tolerate/xcal:startbefore',
            namespaces=ns_map ),
            evt.findtext(
            'ei:eiActivePeriod/xcal:properties/xcal:tolerance/xcal:tolerate/xcal:startafter',
            namespaces=ns_map ) )


# Gets the group IDs of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec\
# Returns: A list of ei:groupID
def get_group_ids(evt, ns_map=NS_A):
    return [e.text for e in evt.iterfind('ei:eiTarget/ei:groupID',namespaces=ns_map)]

# Gets the resource IDs of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: A list of ei:resourceID
def get_resource_ids(evt, ns_map=NS_A):
    return [e.text for e in evt.iterfind('ei:eiTarget/ei:resourceID',namespaces=ns_map)]

# Gets the party IDs of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: A list of ei:partyID
def get_party_ids(evt, ns_map=NS_A):
    return [e.text for e in evt.iterfind('ei:eiTarget/ei:partyID',namespaces=ns_map)]

# Gets the VEN IDs of an event
# evt - etree.Element object
# ns_map - Dictionary of namesapces for OpenADR 2.0; default is the 2.0a spec
# Returns: A list of ei:venID
def get_ven_ids(evt, ns_map=NS_A):
    return [e.text for e in evt.iterfind('ei:eiTarget/ei:venID',namespaces=ns_map)]

