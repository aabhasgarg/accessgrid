#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:
#
# Author:      Everyone
#
# Created:     2003/23/01
# RCS-ID:      $Id: Utilities.py,v 1.9 2003-01-30 23:32:25 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os
import string
import sys
import traceback
import ConfigParser

def LoadConfig(fileName, config={}):
    """
    Returns a dictionary with keys of the form <section>.<option>
    and the corresponding values.
    This is from the python cookbook credit: Dirk Holtwick.
    """
    rconfig = config.copy()
    cp = ConfigParser.ConfigParser()
    cp.optionxform = str
    cp.read(fileName)
    for sec in cp.sections():
        for opt in cp.options(sec):
            rconfig[sec + "."+ opt] = string.strip(cp.get(sec, opt))
    return rconfig

def SaveConfig(fileName, config):
    """
    This method saves the current configuration out to the specified file.
    """
    cp = ConfigParser.ConfigParser()
    cp.optionxform = str
    for k in config.keys():
        (section, option) = string.split(k, '.')
        try:
            cp.set(section, option, config[k])
        except:
            cp.add_section(section)
            cp.set(section, option, config[k])

    cp.write(file(fileName, 'w+'))

def formatExceptionInfo(maxTBlevel=5):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb)

def Which( file ):
    paths = string.split( os.environ['PATH'], os.pathsep )
    if sys.platform == "win32" and string.find( file, ".exe" ) == -1:
        file = file + ".exe"
    for path in paths:
        testfile = os.path.join( path, file )
        if os.path.exists( testfile ):
            return testfile

    return None


def GetResourceList():
    """
    This method reads a file generated by vic and a tcl script
    (courtesy Bob Olson) which contains a vic-compatible description
    of video capture devices on the local machine.  
    Note:  the name of the file is hardcoded
    Note:  for now, the file should be generated at installation, and the
            user should be provided with instructions for generating the 
            file by hand.
           later, users should be able to force generation of the file
            from within the AG software

    An example of the file is as follows:

        device: o100vc.dll - Osprey Capture Card 2
        portnames:  external-in 
        device: Microsoft WDM Image Capture (Win32)
        portnames:  external-in 
        device: o100vc.dll - Osprey Capture Card 1
        portnames:  external-in 

    """
    from AccessGrid.Types import Capability, AGVideoResource
    import fileinput
    import re

    resources = []

    oDeviceMatch = re.compile("^device: (.*)")
    oPortnameMatch = re.compile("^portnames:  (.*[^\s])")

    device = None
    portnames = None
    if os.path.exists("videoresources"):
        for line in fileinput.input("videoresources"):
            match = oDeviceMatch.match(line)
            if match != None:
                device = match.groups()[0]
            match = oPortnameMatch.match(line)
            if match != None:
                portnames = match.groups()

                # assume that, if we have portnames, we already have a device
                resources.append( AGVideoResource( Capability.VIDEO, device, portnames ) )
    else:
        print "Video resources file not found; run device discovery script"

    return resources

