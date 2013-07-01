__author__ = 'Benjamin N. Summerton <bsummerton@enernoc.com>'

# Be sure that we are running this in the root folder
import sys, os
sys.path.insert(0, os.getcwd())

from oadr2 import control, xmpp
import threading
import logging
logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(message)s" )


BASE_URI = 'http://localhost:8080/oadr2-vtn'


def main():
    logging.info('Testing HTTP Transmissions')

    # Setup an instance of the Control Interface
    controller = control.get_instance()

    oadr_config = {'vtn_ids': 'vtn_1,vtn_2,vtn_3,TH_VTN',
              'ven_id':  'ven_py',
              'vtn_uri': BASE_URI,
              'ca_certs': 'ca_certs.pem',
              'auth_private_key': 'rsa_key.pem',
              'http_ca_certs': 'http_ca_certs.pem'}

    pt_config = {
            'user': 'ven_py@localhost/python',
            'password': 'asdf',
            'tmpsavedir': '/tmp',
            'savedir': '/tmp',
            'ca_certs': 'ca_certs.pem',
            'auth_private_key': 'rsa_key.pem',
            'http_ca_certs': 'http_ca_certs.pem'}
     
    xmpper = xmpp.OpenADR2( config = oadr_config )


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


