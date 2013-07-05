# This file is used to run the XMPP module and test XMPP transmissions

__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

# Be sure that we are running this in the root folder
import sys, os
sys.path.insert(0, os.getcwd())

import threading, logging
logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(message)s" )

from oadr2 import xmpp

# Constants
VEN_ID = 'ven_py'
VTN_IDS = 'vtn_1,vtn_2,vtn_3,TH_VTN,vtn_rsa' 
USER_JID = 'ven_py@localhost/python'
USER_PASS = 'asdf'


def main():
    logging.info('Testing XMPP Transmissions')

    config = {
        'user': USER_JID,
        'password': USER_PASS,
        'poll_config': {
            'vtn_poll_interval': 0,
            'ven_id': VEN_ID,
            'vtn_base_uri': '',
            'ven_client_cert_key': None,
            'ven_client_cert_pem': None,
            'vtn_ca_certs': None,
            'event_config': {
                'ven_id': VEN_ID,
                'vtn_ids': VTN_IDS
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


