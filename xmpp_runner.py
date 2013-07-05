# This file is used to run the XMPP module and test XMPP transmissions
__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

# Be sure that we are running this in the root folder
import sys, os
sys.path.insert(0, os.getcwd())

import threading
import logging
logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(message)s" )

from oadr2 import xmpp

# Constants
BASE_URI = 'http://localhost:8080/oadr2-vtn'


def main():
    logging.info('Testing XMPP Transmissions')

    config = {
        'user': 'ven_py@localhost/python',
        'password': 'asdf',
        'poll_config': {
            'vtn_poll_interval': 10,
            'ven_id':  'ven_py',
            'vtn_base_uri': BASE_URI,
            'ven_client_cert_key': None,
            'ven_client_cert_pem': None,
            'vtn_ca_certs': None,
            'event_config': {
                'ven_id': 'ven_py',
                'vtn_ids': 'vtn_1,vtn_2,vtn_3,TH_VTN,vtn_rsa',
            }
        }
    }
     
    xmpper = xmpp.OpenADR2(**config)

    # Some sort of loop thingy here
    _exit = threading.Event()
    print('Running...')
    try:
        while not _exit.is_set():
            _exit.wait(1)
    except:
        logging.info("Interrupted; shutting down...")

    # Clean up the running modules
    xmpper.exit()

    logging.info('========DONE========')


if __name__ == '__main__':
    main()


