#-----------------------------------------------------------------------------
# Name:        NetworkLocation.py
# Purpose:     This object encapsulates the network configuration gunk.
#
# Author:      Ivan R. Judson
#
# Created:     2002/13/12
# RCS-ID:      $Id: NetworkLocation.py,v 1.7 2003-03-24 20:26:12 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class NetworkLocation:
    """
    The Network Locations are simply python objects to manage network
    information. We derive two types, unicast and multicast. It's probably more
    correct to derive IP4Uni and IP4Multi and IP6Uni and IP6Multi, but that's
    an exercise for later.
    """
    TYPE = 'any'
    host = ''
    port = 0

    def __init__(self, host, port):
        self.host = host
        if type(port) != int:
            raise TypeError("Network Location Port must be an int.")
        else:
            self.port = port

    def SetHost(self, host):
        self.host = host

    def GetHost(self):
        return self.host

    def SetPort(self, port):
        if type(port) != int:
            raise TypeError("Network Location Port must be an int.")
        else:
            self.port = port

    def GetPort(self):
        return self.port

    def __repr__(self):
        string = "%s %d" % (self.host, self.port)

class UnicastNetworkLocation(NetworkLocation):
    """
    Unicast network location encapsulates the configuration information about
    a unicast network connection.
    """
    TYPE = 'unicast'
    pass

class MulticastNetworkLocation(NetworkLocation):
    """
    Multicast network location encapsulates the configuration information about
    a multicsat network connection.
    """
    TYPE = 'multicast'
    ttl = 0

    def __init__(self, host=None, port=0, ttl=0):
        if type(ttl) != int:
            raise TypeError("Multicast Network Location TTL must be an int.")
        else:
            self.ttl = ttl

        NetworkLocation.__init__(self, host, port)

    def __repr__(self):
        string = "%s %d %d" % (self.host, self.port, self.ttl)
        return string

    def SetTTL(self, ttl):
        if type(ttl) != int:
            raise TypeError("Multicast Network Location TTL must be an int.")
        else:
            self.ttl = ttl

    def GetTTL(self):
        return ttl
