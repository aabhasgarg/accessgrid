#-----------------------------------------------------------------------------
# Name:        VideoService.py
# Purpose:
#
# Author:      Thomas D. Uram
#
# Created:     2003/06/02
# RCS-ID:      $Id: VideoService.py,v 1.14 2004-09-03 21:47:34 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys, os
try:    import _winreg
except: pass

from AccessGrid.Types import Capability
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter, TextParameter
from AccessGrid import Platform
from AccessGrid.Platform.Config import AGTkConfig, UserConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation

vicstartup="""option add Vic.disable_autoplace %s startupFile
option add Vic.muteNewSources %s startupFile
option add Vic.maxbw 6000 startupFile
option add Vic.bandwidth %d startupFile
option add Vic.framerate %d startupFile
option add Vic.quality %d startupFile
option add Vic.defaultFormat %s startupFile
option add Vic.inputType %s startupFile
option add Vic.device \"%s\" startupFile
option add Vic.defaultTTL 127 startupFile
option add Vic.rtpName \"%s\" startupFile
option add Vic.rtpEmail \"%s\" startupFile
proc user_hook {} {
    global videoDevice inputPort transmitButton transmitButtonState

    update_note 0 \"%s\"

    after 200 {
        set transmitOnStartup %s

        if { ![winfo exists .menu] } {
            build.menu
        }

        if { ![info exists env(VIC_DEVICE)] } {
            set deviceName \"%s\"

            foreach v $inputDeviceList {
                if { [string last $deviceName [$v nickname]] != -1 } {
                    set videoDevice $v
                    select_device $v
                    break
                }
            }
        }
        set inputPort %s
        grabber port %s

        if { $transmitOnStartup } {
            if { [$transmitButton cget -state] != \"disabled\" } {
                set transmitButtonState 1
                transmit
            }
        }
    }
}
"""


def OnOff(onOffVal):
    if onOffVal == "On":
        return "true"
    elif onOffVal == "Off":
        return "false"
    raise Exception,"OnOff value neither On nor Off: %s" % onOffVal


class VideoService( AGService ):

    encodingOptions = [ "h261" ]
    standardOptions = [ "NTSC", "PAL" ]
    onOffOptions = [ "On", "Off" ]

    def __init__( self ):
        AGService.__init__( self )

        self.capabilities = [ Capability( Capability.PRODUCER, Capability.VIDEO ),
                              Capability( Capability.CONSUMER, Capability.VIDEO ) ]
        self.executable = os.path.join('.','vic')
        
        self.profile = None


        #
        # Set configuration parameters
        #

        # note: the datatype of the port parameter changes when a resource is set!
        self.streamname = TextParameter( "streamname", "Video" )
        self.port = TextParameter( "port", "" )
        self.encoding = OptionSetParameter( "encoding", "h261", VideoService.encodingOptions )
        self.standard = OptionSetParameter( "standard", "NTSC", VideoService.standardOptions )
        self.bandwidth = RangeParameter( "bandwidth", 800, 0, 3072 )
        self.framerate = RangeParameter( "framerate", 24, 1, 30 )
        self.quality = RangeParameter( "quality", 75, 1, 100 )
        self.transmitOnStart = OptionSetParameter( "transmitonstartup", "On", VideoService.onOffOptions )
        self.muteSources = OptionSetParameter( "mutesources", "Off", VideoService.onOffOptions )

        self.configuration.append( self.streamname )
        self.configuration.append( self.port )
        self.configuration.append( self.encoding )
        self.configuration.append( self.standard )
        self.configuration.append( self.bandwidth )
        self.configuration.append( self.framerate )
        self.configuration.append (self.quality )
        self.configuration.append (self.transmitOnStart )
        self.configuration.append (self.muteSources )

    def __SetRTPDefaults(self, profile):
        """
        Set values used by rat for identification
        """
        if profile == None:
            self.log.exception("Invalid profile (None)")
            raise Exception, "Can't set RTP Defaults without a valid profile."

        if sys.platform == 'linux2':
            try:
                rtpDefaultsFile=os.path.join(os.environ["HOME"], ".RTPdefaults")
                rtpDefaultsText="*rtpName: %s\n*rtpEmail: %s\n*rtpLoc: %s\n*rtpPhone: \
                                 %s\n*rtpNote: %s\n"
                rtpDefaultsFH=open( rtpDefaultsFile,"w")
                rtpDefaultsFH.write( rtpDefaultsText % ( profile.name,
                                       profile.email,
                                       profile.location,
                                       profile.phoneNumber,
                                       profile.publicId ) )
                rtpDefaultsFH.close()
            except:
                self.log.exception("Error writing RTP defaults file: %s", rtpDefaultsFile)

        elif sys.platform == 'win32':
            try:
                #
                # Set RTP defaults according to the profile
                #
                k = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                    r"Software\Mbone Applications\common")

                # Vic reads these values (with '*')
                _winreg.SetValueEx(k, "*rtpName", 0,
                                   _winreg.REG_SZ, profile.name)
                _winreg.SetValueEx(k, "*rtpEmail", 0,
                                   _winreg.REG_SZ, profile.email)
                _winreg.SetValueEx(k, "*rtpPhone", 0,
                                   _winreg.REG_SZ, profile.phoneNumber)
                _winreg.SetValueEx(k, "*rtpLoc", 0,
                                   _winreg.REG_SZ, profile.location)
                _winreg.SetValueEx(k, "*rtpNote", 0,
                                   _winreg.REG_SZ, str(profile.publicId) )
                _winreg.CloseKey(k)
            except:
                self.log.exception("Error writing RTP defaults to registry")
        

    def Start( self ):
        """Start service"""
        try:

            #
            # Resolve assigned resource to a device understood by vic
            #
            if self.resource == "None":
                vicDevice = "None"
            else:
                vicDevice = self.resource.resource
                vicDevice = vicDevice.replace("[","\[")
                vicDevice = vicDevice.replace("]","\]")

            #
            # Write vic startup file
            #
            startupfile = os.path.join(UserConfig.instance().GetTempDir(),
               'VideoService_%d.vic' % ( os.getpid() ) )

            f = open(startupfile,"w")
            if self.port.value == '':
                portstr = "None"
            else:
                portstr = self.port.value

            if self.muteSources.value == "On":
                # streams are muted, so disable autoplace
                disableAutoplace = "true"
            else:
                # streams are not muted, so don't disable autoplace
                # (flags should not be negative!)
                disableAutoplace = "false"
                
            f.write( vicstartup % ( disableAutoplace,
                                    OnOff(self.muteSources.value),
                                    self.bandwidth.value,
                                    self.framerate.value,
                                    self.quality.value,
                                    self.encoding.value,
                                    self.standard.value,
                                    vicDevice,
                                    "%s(%s)" % (self.profile.name,self.streamname.value),
                                    self.profile.email,
                                    self.profile.email,
                                    OnOff(self.transmitOnStart.value),
                                    vicDevice,
                                    portstr,
                                    portstr ) )
            f.close()

            # Replace double backslashes in the startupfile name with single
            #  forward slashes (vic will crash otherwise)
            if sys.platform == Platform.WIN:
                startupfile = startupfile.replace("\\","/")

            #
            # Start the service; in this case, store command line args in a list and let
            # the superclass _Start the service
            options = []
            options.append( "-u" )
            options.append( startupfile )
            options.append( "-C" )
            options.append( '"' + self.streamname.value + '"'  )
            if self.streamDescription.encryptionFlag != 0:
                options.append( "-K" )
                options.append( self.streamDescription.encryptionKey )
                
            # Check whether the network location has a "type" attribute
            # Note: this condition is only to maintain compatibility between
            # older venue servers creating network locations without this attribute
            # and newer services relying on the attribute; it should be removed
            # when the incompatibility is gone
            if self.streamDescription.location.__dict__.has_key("type"):
                # use TTL from multicast locations only
                if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
                    options.append( "-t" )
                    options.append( '%d' % (self.streamDescription.location.ttl) )
            options.append( '%s/%d' % ( self.streamDescription.location.host,
                                           self.streamDescription.location.port) )
                                           
            # Set the device for vic to use
            os.environ["VIC_DEVICE"] = vicDevice
                                           
            self.log.info("Starting VideoService")
            self.log.info(" executable = %s" % self.executable)
            self.log.info(" options = %s" % options)
            self._Start( options )
            #os.remove(startupfile)
        except:
            self.log.exception("Exception in VideoService.Start")
            raise Exception("Failed to start service")
    Start.soap_export_as = "Start"

    def Stop( self ):
        """Stop the service"""

        # vic doesn't die easily (on linux at least), so force it to stop
        AGService.ForceStop(self)

    Stop.soap_export_as = "Stop"


    def ConfigureStream( self, streamDescription ):
        """Configure the Service according to the StreamDescription"""

        ret = AGService.ConfigureStream( self, streamDescription )
        if ret and self.started:
            # service is already running with this config; ignore
            return

        # if started, stop
        if self.started:
            self.Stop()

        # if enabled, start
        if self.enabled:
            self.Start()
    ConfigureStream.soap_export_as = "ConfigureStream"

    def SetResource( self, resource ):
        """Set the resource used by this service"""

        self.log.info("VideoService.SetResource : %s" % resource.resource )
        self.resource = resource
        if "portTypes" in self.resource.__dict__.keys():

            # Find the config element that refers to "port"
            try:
                index = self.configuration.index(self.port)
                found = 1
            except ValueError:
                found = 0

            # Create the port parameter as an option set parameter, now
            # that we have multiple possible values for "port"
            # If self.port is valid, keep it instead of setting the default value.
            if ( isinstance(self.port, TextParameter) or isinstance(self.port, ValueParameter) ) and self.port.value != "" and self.port.value in self.resource.portTypes:
                self.port = OptionSetParameter( "port", self.port.value,
                                                             self.resource.portTypes )
            else:
                self.port = OptionSetParameter( "port", self.resource.portTypes[0],
                                                             self.resource.portTypes )

            # Replace or append the "port" element
            if found:
                self.configuration[index] = self.port
            else:
                self.configuration.append(self.port)

    SetResource.soap_export_as = "SetResource"

    def SetIdentity(self, profile):
        """
        Set the identity of the user driving the node
        """
        log.info("SetIdentity: %s %s", profile.name, profile.email)
        self.profile = profile
        self.__SetRTPDefaults(profile)
    SetIdentity.soap_export_as = "SetIdentity"

if __name__ == '__main__':

    from AccessGrid.AGService import AGServiceI, RunService

    service = VideoService()
    serviceI = AGServiceI(service)
    RunService(service,serviceI,int(sys.argv[1]))
