# Some Unit-Tests for the Event Handler (2.0a spec)
__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

# NOTE: Make sure to run this file from the root directory of the project
import sys,os
sys.path.insert( 0, os.getcwd() )
xml_dir = os.path.join( os.path.dirname(__file__), 'xml_files')

from oadr2 import event
from lxml import etree
import unittest

# Some constants
SCHEMA_DIR = os.path.join(xml_dir, '2.0a_schema/')
SAMPLE_DIR = os.path.join(xml_dir, '2.0a_spec/')
VEN_ID = 'ven_py'
STATUS_CODES = [200, 403, 405]



class EventHandlerTest(unittest.TestCase):

    def setUp(self):
        self.start_thread = False

        # Some configureation variables, by default, this is for the a handler
        self.config = {'vtn_ids': 'vtn_1,vtn_2,vtn_3,TH_VTN',
                       'ven_id': VEN_ID}
        oadr_schema_file = open(os.path.join(SCHEMA_DIR, 'oadr_20a.xsd'))        # OpenADR
        oadr_schema_doc = etree.parse(oadr_schema_file)
        self.oadr_schema = etree.XMLSchema(oadr_schema_doc)
        self.event_handler = event.EventHandler(**self.config)
        
        # Make things a little nicer for us to see
        print('')
        print(40 * '=')


    def tearDown(self):
        pass


    def test_build_request_payload(self):
        print('in test_build_request_payload()')

        # Generate the payload
        payload = self.event_handler.build_request_payload()
#        print('XML generated:')
#        print(etree.tostring(payload, pretty_print=True))

        # Validate the schema
        print('Testing against OADR Schema.')
        self.assertTrue(self.oadr_schema.validate(payload), msg='Schema didn\'t validate for build_request_payload().')
        print('OK')

        # Check the VEN ID to make sure it's ours
        print('Checking VEN ID')
        ven_id = payload.findtext('pyld:eiRequestEvent/ei:venID',namespaces=self.event_handler.ns_map)
        self.assertEqual(ven_id, VEN_ID, msg='VEN ID for genrated payload did not match')
        print('OK')
        print('build_request_payload() OK')


    def test_build_error_response(self):
        print('in test_build_error_response')
        request = 'req_1'
        code = '404'            # Breaks when is a pure integer, must be turned into a string
        desc = 'HI MOM !!1!'

        # Generate a sample payload to play with
        payload = self.event_handler.build_error_response(request, code, desc)
#        print('XML generated:')
#        print(etree.tostring(payload, pretty_print=True))

        # Validate the schema
        print('Testing against OADR schema.')
        self.assertTrue(self.oadr_schema.validate(payload), msg='Schema didn\'t validate for build_error_response().')
        print('OK')

        # Make sure it's generating the correct data
        # Right now the function only adds in the error code and the ven's ID
        err_code = payload.findtext('pyld:eiCreatedEvent/ei:eiResponse/ei:responseCode', namespaces=self.event_handler.ns_map)
        ven_id = payload.findtext('pyld:eiCreatedEvent/ei:venID', namespaces=self.event_handler.ns_map)
        print('Testing VEN ID')
        self.assertEqual(ven_id, VEN_ID, msg='VEN ID for generated payload did not match; ven_id=%s, VEN_ID=%s'%(ven_id, VEN_ID))
        print('OK')
        print('Testing Error Code')
        self.assertEqual(err_code, code, msg='Error code for generated payload did not match; err_code=%s, code=%s'%(err_code, code))
        print('OK')

        # TODO: check for a description if we have set one
        if desc is not None:
            pass

        print('build_error_response() OK')


    def test_build_created_payload(self):
        print('in test_build_created_payload()')
        
        # Make some sample events
        #        [(e_id,e_mod_num,requestID,opt,status), ...]
        events = [('event_1', '0', 'req_1', 'optIn', '200'),
                  ('event_2', '0', 'req_2', 'optOut', '403'),
                  ('event_3', '2', 'req_87', 'optOut', '405'),
                  ('event_asdf', '56', 'req_asdf', 'optIn', '200'),
                  ('event_FDSA', '1', 'req_reset', 'optIn', '200')]

        print('Building Event Payload')
        payload = self.event_handler.build_created_payload(events)
        print('OK')
#        print('Generated XML:')
#        print(etree.tostring(payload, pretty_print=True))

        print('Testing payload against schema')
        self.assertTrue(self.oadr_schema.validate(payload), msg='build_created_payload()\'s XML is not valid')
        print('OK')

        # Make sure all the data that we put in we will get back out
        print('Testing input data vs payload data')
        i = 0
        for res in payload.iterfind('pyld:eiCreatedEvent/ei:eventResponses/ei:eventResponse', namespaces=self.event_handler.ns_map):
            # Yank data
            res_code = res.findtext('ei:responseCode', namespaces=self.event_handler.ns_map)
            res_id = res.findtext('pyld:requestID', namespaces=self.event_handler.ns_map)
            e_id = res.findtext('ei:qualifiedEventID/ei:eventID', namespaces=self.event_handler.ns_map)
            mod_num = res.findtext('ei:qualifiedEventID/ei:modificationNumber', namespaces=self.event_handler.ns_map)
            opt = res.findtext('ei:optType', namespaces=self.event_handler.ns_map)
            
            # Run the assertion tests
            print('Event: ' + events[i][0])
            self.assertEqual(events[i][0], e_id, msg='Event ID is not the same; desired=%s, got=%s'%(events[i][0], e_id))
            self.assertEqual(events[i][1], mod_num, msg='Mod Number is not the same; desired=%s, got=%s'%(events[i][1], mod_num))
            self.assertEqual(events[i][2], res_id, msg='Request ID does not match up; desired=%s, got=%s'%(events[i][2], res_id))
            self.assertEqual(events[i][3], opt, msg='Opt status is not the same; desired=%s, got=%s'%(events[i][3], opt))
            self.assertEqual(events[i][4], res_code, msg='Status code is not the same; desired=%s, got=%s'%(events[i][4], res_code))

            i += 1
        print('All OK') # Everything went better than expected.
        print('All events have the same supplied information')

        print('build_created_payload() OK')


    def test_handle_payload(self):
        print('in test_handle_payload()')

        # The files that we want to test against
        files = [#'sample_oadrDistributeEvent.xml',             # First file generates validation errors, due to 'description' field
                 'sample_oadrDistributeEvent_W_no_targets.xml',
                 'sample_oadrDistributeEvent_W_something.xml'
                 ]

        # Load up each individual file
        for filename in files:
            xml_file = open(os.path.join(SAMPLE_DIR, filename))
            xml_doc = etree.XML(xml_file.read())
#            print('XML for "%s":'%(filename))
#            print(etree.tostring(xml_doc, pretty_print=True))   # Make sure it read in correctly
            print('Validating')
            self.assertTrue(self.oadr_schema.validate(xml_doc), msg='Validation falied for %s'%(filename))
            print('OK')

            # send the xml file to the payload handler
            print('Sending sample XML to payload handler')
            payload = self.event_handler.handle_payload(xml_doc)
            print('OK')
            
            if payload is not None:
#                print('Return payload:')
#                print(etree.tostring(payload, pretty_print=True))

                # See if what we got back was valid itself
                print('Validating response payload')
                self.assertTrue(self.oadr_schema.validate(payload), msg='Return payload failed for %s'%(filename))
                print('OK')

            else:
                print('Payload was not generated')

            # Do this at the end of the loop
            print('+' * 4)

        print('handle_payload() OK')


    # Tests Batch A from the sample XML files; used for events w/ changing mod numbers
    def test_batch_a(self):
        print("in test_batch_a()")

        # The files
        files = ['batch_a_1.xml', 'batch_a_2.xml', 'batch_a_3.xml', 'batch_a_4.xml']

        # Some other stuff 
        e_id = 'e_1'
        mod_nums = [0, 1, 2, 4]
        i = 0        

        # Load up each file
        for filename in files:
            xml_file = open(os.path.join(SAMPLE_DIR, filename))
            xml_doc = etree.XML(xml_file.read())
            self.assertTrue(self.oadr_schema.validate(xml_doc), msg='Validation failed for "%s"'%(filename))
            print('"%s" is valid; Testing it against the payload handler.'%(filename))

            # Send it the message and generate a payload
            payload = self.event_handler.handle_payload(xml_doc)

            # Grab an event from self._events via the stateful methods, and check mod numbers
            evt = self.event_handler.get_event(e_id)
            mod_num = event.get_mod_number(evt)
            self.assertEqual(mod_num,  mod_nums[i], msg='Mod number not the same! got=%d, should be=%d'%(mod_num, mod_nums[i]))
            print('Mod number same.')

            # Check the payload
            if payload is not None:
                self.assertTrue(self.oadr_schema.validate(payload), msg='Return payload failed for %s'%(filename))
#                print('Return payload for "' + filename + '" is valid.')
#                print(etree.tostring(payload, pretty_print=True))
            else:
                print('No return payload generated for "%s"'%(filename))

            print ('+' * 4)
            i += 1

        print('test_batch_a() OK')


    # Test Batch B from the sample XML files; send an event, send a 2nd with a higher mod num,
    # then send one with a lower mod.
    # Similar in structure to test_batch_a()
    def test_batch_b(self):
        print('in test_batch_b()')

        # The files
        files = ['batch_b_1.xml', 'batch_b_2.xml', 'batch_b_3.xml']

        # Some other stuff 
        e_id = 'e_1'
        mod_nums = [0, 5, 3]
        i = 0                   # Just an index for us

        # Load up each file
        for filename in files:
            xml_file = open(os.path.join(SAMPLE_DIR, filename))
            xml_doc = etree.XML(xml_file.read())
            self.assertTrue(self.oadr_schema.validate(xml_doc), msg='Validation failed for "%s"'%(filename))
            print('"%s" is valid; Testing it against the payload handler.'%(filename))

            # Send it the message and generate a payload
            payload = self.event_handler.handle_payload(xml_doc)

            # Grab an event from self._events via the stateful methods, and check mod numbers
            evt = self.event_handler.get_event(e_id)
            mod_num = event.get_mod_number(evt)
          
            # Make sure we hit the 'else' on the third itteration
            if i != 2:
                self.assertEqual(mod_num,  mod_nums[i], msg='Mod number not the same! got=%d, should be=%d'%(mod_num, mod_nums[i]))
            else:
                self.assertNotEqual(mod_num, mod_nums[i], msg='Not good, the mod numbers are the same')
                print('Don\'t worry about that warning, it\'s what we want.')

            print('Expected Mod Number gotten.')

            # Check the payload
            if payload is not None:
                self.assertTrue(self.oadr_schema.validate(payload), msg='Return payload failed for %s'%(filename))
                print('Return payload for "%s" is valid.'%(filename))
            else:
                print('No return payload generated for "%s"'%(filename))

            print ('+' * 4)
            i += 1
        
        print('test_batch_b() OK')
        

    # Test batch c; test for targets.  We will need to construct another handler or two
    def test_batch_c(self):
        # This test will have 8 xml files, 4 w/ valid target ids, 4 that are not.
        # The first four are OK, but the other's aren't.
        print('in test_batch_d()')
        
        # A little key:
        # 1 = good venID            ven_py
        # 2 = good resourceID       Resource_123
        # 3 = good partyID          Party_123
        # 4 = good groupId          Group_123
        # 5 .. 8 follow the same pattern, but all are bad!

        #Override the current one with some new settings
        self.config['resource_id'] = 'Resource_123'
        self.config['party_id'] = 'Party_123'
        self.config['group_id'] = 'Group_123'
        self.event_handler = event.EventHandler(**self.config)

        # Start looping through
        i = 1
        for i in range(1, 9):
            # Open the file and validate the XML
            xml_file = open(os.path.join(SAMPLE_DIR, 'batch_c_%i.xml'%(i)))
            xml_doc = etree.XML(xml_file.read())
            self.assertTrue(self.oadr_schema.validate(xml_doc), msg='Validation falied for "batch_c_%i.xml"'%(i))
            print('"batch_c_%i.xml" is valid.'%(i))

            # Send it to the handler
            payload = self.event_handler.handle_payload(xml_doc)
            if payload is not None:
#                print(etree.tostring(payload, pretty_print=True))
                # Get some data
                status_code = payload.findtext('pyld:eiCreatedEvent/ei:eventResponses/ei:eventResponse/ei:responseCode', namespaces=self.event_handler.ns_map)
                opt_type = payload.findtext('pyld:eiCreatedEvent/ei:eventResponses/ei:eventResponse/ei:optType', namespaces=self.event_handler.ns_map)

                # First 4 should be '200' and 'optIn', else should be '403' and 'optOut'
                if i <= 4:
                    self.assertEqual(status_code, '200', msg='Status code is not \'200\' for "batch_c_%i.xml"'%(i))
                    self.assertEqual(opt_type, 'optIn', msg='Opt type is not \'optIn\' for "batch_c_%i.xml"'%(i))
                    print('Status Code and Opt Type are OK')
                else:
                    self.assertEqual(status_code, '403', msg='Status code is not \'403\' for "batch_c_%i.xml"'%(i))
                    self.assertEqual(opt_type, 'optOut', msg='Opt type is not \'optOut\' for "batch_c_%i.xml"'%(i))
                    print('Status Code and Opt Type are OK')
                    
            else:
                print('Payload for "batch_c_%i.xml"'%(i))

            print('+' * 4)


        print('test_batch_d() OK')



if __name__ == '__main__':
    unittest.main()

