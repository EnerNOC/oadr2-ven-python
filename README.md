# EnerNOC Open Source Python VEN #


This package is a implementation of the [OpenADR](http://openadr.org) 2.0a VEN 
(end node) client.  It *should* pass most of the 2.0a certification test 
suite.  The package includes both an HTTP poll client and XMPP client (even 
though 2.0a doesn't technically support XMPP.)  

There is also some code to handle 2.0b payloads for the Event service, although
this is not complete.


## Structure: ##

The main files for this app are in the ./oadr2 directory, they are:

 * `./oadr2/schedule.py`    *Datestring interpretation*
 * `./oadr2/event.py`       *Event Handler modulea*
 * `./oadr2/control.py`     *Controller module (Hardware related)*
 * `./oadr2/poll.py`        *HTTP handler of OpenADR events*
 * `./oadr2/xmpp.py`        *XMPP handler of OpenADR events*


## Installation & Setup: ##

This package was developed under python 2.7 but it should work under 3.x as well.

We recommend you use [`virtualenv`](http://www.virtualenv.org/) to manage your 
environment although it's not required. 

The application depends on the following third-party packages:

 * `lxml`             *Python "libXML" wrapper*
 * `sleekxmpp`        *XMPP client library*
 * `dnspython`        *Optional package for sleekxmpp to perform DNS srv lookups*

To see the exact versions, check the file `requirements.txt`.  If you use 
[`pip`](https://pypi.python.org/pypi/pip) you can install the requirements by 
running:

    $ pip install -r requirements.txt


## Running the clients ##

There are four main executable files in this app, they are:

 * `poll_runner.py`
 * `xmpp_runner.py`
 * `test/event_unittest.py`
 * `test/event_b_unittest.py`

The `poll_runner.py` script is used to test OpenADR2 over HTTP, where as
`xmpp_runner.py` is for XMPP.  To run either of the two scripts, just use
`python` on one of the scripts:

    $ python xmpp_runner.py

To end a script at any time, you can send a interrupt signal via ^C or Ctrl-C
(in its terminal window).

Inside of `poll_runner.py` and `xmpp_runner.py` there are configuration
options for each script.  Make sure to alter these to your needs before running
anything.


##### For `./poll_runner.py`: #####

 * Change `BASE_URI` to point to the address (and port) of your VTN's base URL.
   Make sure to include `http://` or `https://` in the URL string.  There are also 
   extra constants where you can specify paramters for authentication certificates.
 * Change `VEN_ID` to an identifier that your VTN knows about.
 * Change `VTN_IDS` to a CSV string of your VTN(s) identifiers.
 * Change `VTN_POLL_INTERVAL` how often the VEN will poll the VTN with an
   `oadrRequestEvent` payload.  Time is in seconds.

##### For `./xmpp_runner.py`: #####

 * Change `VEN_ID` to an identifier that your VTN knows about.
 * Change `VTN_IDS` to a CSV string of your VTN(s) identifiers.
 * Change `USER_JID` to the JabberID you want to VEN to use when connecting to
   an XMPP server.  It is recommended that you specify a resource as well
   (e.g. '/python').
 * Change `USER_PASS` to the password for the associated JID.

If you do not have an XMPP server, there are a number of open source servers, 
including [OpenFire](http://www.igniterealtime.org/projects/openfire/), 
[Ejabberd](http://www.ejabberd.im/) and [Prosody](http://prosody.im/).  


To run a VTN, we recommend the [EnerNOC open source VTN project](/EnerNOC/oadr2-vtn-new) 
which supports XMPP and OpenADR 2.0a.  Alternately, you can simulate
VTN payloads using the XML console in the [Psi XMPP client](http://psi-im.org/).


### OpenADR 2.0b

Please note that while this software should be able to handle 2.0b (OpenADR)
payloads, most of it is hard-coded to work with the 2.0a specification. Though
if you want to run it under 2.0b, it should not be too difficult make it do so.
The simpliest way is as follows:

 * In `./oadr2/event.py,` in the `__init__()` function of the `EventHandler`
   class, change the default value of `oadr_profile_level` to:
   `OADR2_PROFILE_20A`
    
 * In `./oadr2/xmpp.py` in the `__init__()` function of the `OADR2Message`
   class, change the default value of `oadr_profile_level` to:
   `event.OADR2_PROFILE_20B` *(don't forget that `event.` in front)*.

The other two executable scripts are in the ./test directory, they are for unit
testing purposes.  Mainly to test the `EventHandler` class.
`./test/event_unittest.py` is a generic test of handing and processing the XML
payloads, and `./test/event_b_unittest.py` is similar, except that it runs the
2.0b spec (of OpenADR).  

All scripts should be run with the working directory at the base directory
of this project like so:

    python test/event_unittest.py



## License: ##

This code is released under the Apache 2.0 Open Source license. See the 
LICENSE file for details.


## Credits: ##

This software was created by EnerNOC's Advanced Technology team, the authors
are:
 * Thom Nichols   <tnichols@enernoc.com>
 * Ben Summerton  <bsummerton@enernoc.com>


