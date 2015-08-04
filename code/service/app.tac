#!usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2012 Wyss Institute at Harvard University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

http://www.opensource.org/licenses/mit-license.php
"""

# run with twistd -noy app.tac
# see http://twistedmatrix.com/documents/current/core/howto/application.html

from twisted.internet import reactor
from twisted.application import internet, service
from twisted.web import server
from twisted.web.wsgi import WSGIResource

from flaskapp import flaskapp

from experimentcore.exp_dbifc import setupExperiment

flaskapp.app.wsport = 9000  # port for websocket
wsgiAppAsResource = WSGIResource(reactor, reactor.getThreadPool(), flaskapp.app)
application = service.Application("FlaskTwisted webserver")
my_server = internet.TCPServer(8080, server.Site(wsgiAppAsResource))
my_server.setServiceParent(application)

from websocket.datapush import startDataPushServer
dps_factory, dps_listening_port = startDataPushServer(port=flaskapp.app.wsport)
a = setupExperiment("evolvulator", control_on=True, datapush=dps_factory, debug=True)
