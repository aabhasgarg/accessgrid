#-----------------------------------------------------------------------------
# Name:        CoherenceService.py
# Purpose:     This service provides coherence among the Venues Clients and
#               the virtual venue. Each venue client connects to this service.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CoherenceService.py,v 1.12 2003-01-22 20:28:52 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import socket
from threading import Thread
import sys
from SocketServer import ThreadingTCPServer
from SocketServer import ThreadingMixIn, StreamRequestHandler

from pyGlobus.io import GSITCPSocketServer

from NetworkLocation import UnicastNetworkLocation

def auth_callback(arg, handle, identity, context):
    print "In the Authorization Callback"
    return 1

# This really should be defined in pyGlobus.io
class ThreadingGSITCPSocketServer(ThreadingMixIn, GSITCPSocketServer): pass

class CoherenceRequestHandler(StreamRequestHandler):
    """
    The CoherenceRequestHandler is the object than handles a single coherence
    connection. This is an attempt to use the ThreadedTCPServer so that I can
    easily change to a GSI TCP solution.
    """
    def stop(self):
        self.running = 0
    
    def send(self, data):
        self.request.send(data)
        
    def handle(self):
        # register setup stuff
#        print "Saving connection! ", str(self)
        self.server.connections.append(self)
        
        # loop getting data and handing it to the server
        self.running = 1
        while(self.running == 1):
#            print "Reading data!"
            try:
                data = self.rfile.readline()
#                print "Read %s" % data[:-1]
                self.server.distribute(data)
            except:
                print "Caught exception trying to read data"
                self.running = 0
                self.server.connections.remove(self)
                
#class CoherenceService(ThreadingTCPServer):
class CoherenceService(ThreadingGSITCPSocketServer, Thread):
    """
    The CoherenceService provides a secure event layer. This might be more 
    scalable as a secure RTP or other UDP solution, but for now we use TCP.
    In the TCP case the CoherenceService is the Server.
    """
    def __init__(self, server_address, 
                 RequestHandlerClass=CoherenceRequestHandler):
        Thread.__init__(self)
        self.connections = []
        ThreadingGSITCPSocketServer.__init__(self, server_address, RequestHandlerClass)
#        ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)

    def run(self):
        self.running = 1
        while(self.running):
            self.handle_request()

    def stop(self):
        self.running = 0
        
    def distribute(self, data):
        for c in self.connections:
            c.wfile.write(data)
            

            
if __name__ == "__main__":
  import string
  host = string.lower(socket.getfqdn())
  port = 6500
  print "Creating new CoherenceService at %s %d." % (host, port)
  coherence = CoherenceService((host, port), CoherenceRequestHandler)
  coherenceThread = threading.Thread(target=coherence.run)
  coherenceThread.start()