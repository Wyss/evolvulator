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

"""
webservertest.tac
You can run this .tac file directly with:
   twistd -ny webservertest.tac

"""

from twisted.web import server, resource, static
from twisted.application import internet, service
from os.path import dirname, basename, split, abspath
from experimentloop import ExperimentLoop

class Foo(resource.Resource):
    def render_GET(self, request):
        return "hello world yo " + ', prepath: ' + \
                    str(request.prepath) + \
                    ', args: ' + str(request.args) 
        
    def render_POST(self, request):
        return "hello world"

# serve up this directory
this_dirname, this_filename = split(abspath(__file__))
root = static.File(this_dirname)
root.putChild("foo", Foo())

application = service.Application("Basic webserver")
server = internet.TCPServer(8080, server.Site(root))
server.setServiceParent(application)

testIP = "10.11.32.226"
a = ExperimentLoop('http://'+ testIP + '/jsonAnalog', 2)
a.start()