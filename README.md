EnerNOC's Open Source Python VEN
--------------------------------

License:
========
    Please see the file ./LICENSE for information regarding licensing of this
    application.

----------------

Credits:
========
    This software was created by EnerNOC's Advanced Technology team, the authors
    are:
        Thom Nichols   <tnichols@enernoc.com>
        Ben Summerton  <bsummerton@enernoc.com>

----------------

Structure:
==========
    The main files for this app are in the ./oadr2 directory, they are:
        ./oadr2/schedule.py -> Datestring interpretation
        ./oadr2/event.py    -> Event Handler module
        ./oadr2/control.py  -> Controller module (Hardware related)
        ./oadr2/poll.py     -> HTTP handler of OpenADR events
        ./oadr2/xmpp.py     -> XMPP handler of OpenADR events

    Files in the ./test directory relate to unit tests.  And the folders ./bin,
    ./lib, ./include are for Python's "virtualenv."

----------------

How-To:
=======
    Make sure that the python version you are using is 2.7; this application as
    developed using 2.7.2.

    Before using, it is recommended that you have an application called
    "virtualenv," installed.  To start the virtual python environment, in the
    root directory type:
        $ source ./bin/activate

    To shutdown virtualenv type:
        $ deactivate

    The application depends on three third-party python packages:
        lxml       ->  Python "libXML," wrapper
        sleekxmpp  ->  Package for writing XMPP clients 
        wsgreif    ->  Package for Web Server Gateway Interface (WSGI)

    To see the exact versions, check the file ./requirements.txt.

    There are four main executable files in this app, they are:
        ./poll_runner.py
        ./xmpp_runner.py
        ./test/event_unittest.py
        ./test/event_b_unittest.py

    The poll_runner.py script is used to test OpenADR2 over HTTP, where as
    xmpp_runner.py is for XMPP.  To run either of the two scripts, just use
    "python," on one of the scripts
        $ python xmpp_runner.py

    To end a script at any time, you can send a interrupt signal via ^C or
    Ctrl-C (in its terminal window).

    Inside of ./poll_runner.py and ./xmpp_runner.py there are configuration
    options for each script.  Make sure to alter these to your needs before
    running anything.

    For ./poll_runner.py:
      + Change "BASE_URI," to point to the address (and port) of your VTN's base
        URL.  Make sure to include the "http://" in the string.  There are also
        extra constants where you can specify paramters for authentication
        certificates.
      + Change "VEN_ID," to an identifier that your VTN knows about.
      + Change "VTN_IDS," to a CSV string of your VTN(s) identifiers.
      + Change "VTN_POLL_INTERVAL," how often the VEN will poll the VTN with an
        oadrRequestEvent payload.  Time is in seconds.

    For ./xmpp_runner.py:
      + Change "VEN_ID," to an identifier that your VTN knows about.
      + Change "VTN_IDS," to a CSV string of your VTN(s) identifiers.
      + Chnage "USER_JID," to the JabberID you want to VEN to use when
        connecting to the XMPP server.  It is recommended that you specify a
        resource as well (e.g. '/python').
      + Change "USER_PASS," to the password for the associated JID.

    If you do not have an XMPP server, a suggested one to download and run is
    "OpenFire."  It was the type of server that this code was tested on.  Also,
    if you do not have a VTN that can connect to an XMPP server, it is suggested
    that you use a program called "Psi," to deliver oadrDistributeEvent
    payloads via its "XML Console."

    Please note that while this software should be able to handle 2.0b (OpenADR)
    payloads, most of it is hard-coded to work with the 2.0a specification.
    Though if you want to run it under 2.0b, it should not be too difficult make
    it do so.  The simpliest way is as follows:
        
      + In ./oadr2/event.py, in the "__init__()," function of the EventHandler
      class, change the default value of "oadr_profile_level," to:
            OADR2_PROFILE_20A
    
      + In ./oadr2/xmpp.py, in the "__init__()," function of the OADR2Message
      class, chnage the default value of "oadr_profile_level," to:
            event.OADR2_PROFILE_20B

            (Don't forget to add 'event.' in front.)

    The other two executable scripts are in the ./test directory, they are for
    unit testing purposes.  Mainly to test the EventHandler class.
    ./test/event_unittest.py is a generic test of handing and processing the XML
    payloads, and ./test/event_b_unittest.py is similar, except that it runs the
    2.0b spec (of OpenADR).  They are run just the same as the "runner,"
    scripts.

    Please make sure run all of the scripts in the root directory of this
    application.

----------------

Final:
======
    
    Thank you for your interest in the application.  Have fun and enjoy.

----------------


