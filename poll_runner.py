# A file or something to test the poll.py module for OpenADR 2.0ab
__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com'

# Make sure to run this from the root directory
import sys, os
sys.path.insert(0, os.getcwd())

import threading

import logging
logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(message)s" )

from oadr2 import control, event, poll

BASE_URI = 'http://localhost:8080/oadr2-vtn'

CLIENT_CERT_KEY_PATH = None #'./ven_key.pem'
CLIENT_CERT_PATH = None #'./ven_cert.pem'
TRUST_CERTS = None #'./oadr_trust_certs.pem'

def main():
    logging.info('Testing XMPP Transmisssions')

    # Make an instance of the Control Interface
    controller = control.get_instance()

    # TODO: Add in something for the 2.0b spec later
    config = {'vtn_ids': 'vtn_1,vtn_2,vtn_3,TH_VTN,vtn_rsa',
              'interval': 10,
              'ven_id':  'ven_py',
              'vtn_uri': BASE_URI,
              'ven_client_cert_key': CLIENT_CERT_KEY_PATH,
              'ven_client_cert_pem': CLIENT_CERT_PATH,
              'vtn_ca_certs': TRUST_CERTS
              }
     
    poller = poll.OpenADR2(config=config)

    # Some sort of loop thingy here
    print('Running...')
    _exit = threading.Event()
    try:
        while not _exit.is_set():
            _exit.wait(1)
    except:
        pass

    # Close the poller
    print('Exiting the OpenADR 2 poller')
    poller.exit()

    print('========DONE========')


if __name__ == '__main__':
    main()


