from twisted.internet import reactor
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS
from collections import defaultdict
import json
import traceback
class DataPushServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)
    # end def

    def onMessage(self, msg, binary):
        if not binary:
            self.factory.emit("'%s' from %s" % (msg, self.peerstr))
    # end def

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)
    # end def
# end class

class DataPushServerFactory(WebSocketServerFactory):
    """
    One Data push server can support many different connections
    """
    protocol = DataPushServerProtocol

    def __init__(self, url, debug=False):
        WebSocketServerFactory.__init__(self, url)
        # push data spefic to a particular path from a resource URI
        # see autobahn.websocket.ConnectionRequest for an example
        # of the different information available 
        self._debug = debug
        self.uri_map_to_clients = {}
    # end def

    def register(self, client):
        # print "THE PATH to worry about", client.http_request_path, client.peerstr, client
        # omit the leading slash /
        path_key = client.http_request_path[1:]
        if path_key in self.uri_map_to_clients:
            clients = self.uri_map_to_clients[path_key]
            if not client in clients:
                print "registered client " + client.peerstr
                clients.append(client)
    # end def

    def unregister(self, client):
        # omit the leading slash /
        path_key = client.http_request_path[1:]
        if path_key in self.uri_map_to_clients:
            clients = self.uri_map_to_clients[path_key]
            if client in clients:
                print "unregistered client " + client.peerstr
                clients.remove(client)
        else:
            print "client not unregistered"
    # end def
    
    def addURI(self, uri_path):
        if not uri_path in self.uri_map_to_clients:
            self.uri_map_to_clients[uri_path] = []
    # end def
    
    def removeURI(self, uri_path):
        if uri_path in self.uri_map_to_clients:
            del self.uri_map_to_clients[uri_path]
    # end def

    def emit(self, path, msg):
        clients = self.uri_map_to_clients[path]
        if self._debug:
            print "broadcasting message '%s' .." % msg
        for c in clients:
            if self._debug:
                print "send to " + c.peerstr
            print json.dumps(msg)
            c.sendMessage(json.dumps(msg))
    # end def
# end class

def startDataPushServer(ip='localhost', port=9000):
    """
    returns a tuple containing  the factory and the listening port
    """
    factory = DataPushServerFactory("ws://" + ip + ":" + str(port), debug = True)
    # listenWS returns twisted.internet.interfaces.IListeningPort
    # http://twistedmatrix.com/documents/current/api/twisted.internet.interfaces.IListeningPort.html
    return (factory, listenWS(factory))