#-----------------------------------------------------------------------------
# Name:        SharedPDF.py
# Purpose:     Shared PDF viewer for Windows platform.
#
# Author:      Susanne Lefvert
#
# Created:     $Date: 2005-04-06 20:50:38 $
# RCS-ID:      $Id: SharedPDF.py,v 1.2 2005-04-06 20:50:38 lefvert Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# wxPython imports
from wxPython.wx import *

if wxPlatform == '__WXMSW__':
    from wx.lib.pdfwin import PDFWindow

# AGTk imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.SharedAppClient import SharedAppClient
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid import icons
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid.DataStoreClient import GetVenueDataStore

# Standard imports
import os
import getopt
import sys

class PdfViewer(wxPanel):
    '''
    Shared application that uses the ActiveX interface to
    Adobe Acrobate Reader version 4 and higher. This
    application only works on Windows platforms. It uses
    the defined pdf activex class provided by wxPython.
    '''
    
    def __init__(self, parent, name, appUrl, venueUrl):
        wxPanel.__init__(self, parent, -1)

        # Create ActiveX interface to adobe acrobate reader
        self.pdf = PDFWindow(self)
        
        # Do UI layout
        self.__Layout()
    
        # Create UI events
        EVT_BUTTON(self, self.openButton.GetId(), self.OnOpenButton)
        EVT_BUTTON(self, self.prevButton.GetId(), self.OnPrevPageButton)
        EVT_BUTTON(self, self.nextButton.GetId(), self.OnNextPageButton)
        EVT_WINDOW_DESTROY(self, self.OnExit)

        # Create shared application client        
        self.sharedAppClient = SharedAppClient(name)
        self.log = self.sharedAppClient.InitLogging()
        self.id = self.sharedAppClient.GetPublicId()
        self.log.debug("PdfViewer.__init__: Start pdf viewer, venueUrl: %s, appUrl: %s"%(venueUrl, appUrl))

        # Get client profile
        clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(), "profile")
        clientProfile = ClientProfile(clientProfileFile)

        # Join the application session.
        self.sharedAppClient.Join(appUrl, clientProfile)
        
        # Register callbacks for external events
        self.sharedAppClient.RegisterEventCallback("open", self.OpenCallback)
        self.sharedAppClient.RegisterEventCallback("position", self.ChangePositionCallback)

        # Create data store interface
        self.dataStoreClient = GetVenueDataStore(venueUrl)
        
        # Get current state
        ret = self.sharedAppClient.GetData("position")
        self.file = None
        self.pageNr = 1
      
        if ret:
            self.file, self.pageNr = ret
            try:
                self.dataStoreClient.Download(self.file, "tmp")
                self.pdf.LoadFile("tmp")
                self.pdf.setCurrentPage(self.pageNr)
            except:
                self.log.exception("PdfViewer.__init__: Download failed %s"%(self.file))

        self.Layout()
        self.Show()

    #
    # Callbacks for local UI events.
    #

    def OnOpenButton(self, event):
        '''
        Invoked when user clicks the open button.
        '''
        dlg = FileSelectorDialog(self, -1, "Select File Location", self.dataStoreClient)

        if dlg.ShowModal() == wxID_OK:
            selectedFile = dlg.GetFile()
            if selectedFile:
                wxBeginBusyCursor()

                # Get file from venue
                try:
                    self.dataStoreClient.Download(selectedFile, "tmp")
                    self.pdf.LoadFile("tmp")
                    self.pageNr = 1
                    self.file = selectedFile

                except:
                    self.log.exception("PdfViewer.OnOpenButton: Failed to download %s"%(selectedFile))
                    dlg = wxMessageDialog(frame, 'Failed to download %s.'%(selectedFile),
                                          'Download Failed', wxOK | wxICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()

                else:
                    # Update shared app status
                    self.sharedAppClient.SetData("position", (self.file, self.pageNr))
                    
                    # Send event
                    self.sharedAppClient.SendEvent("load", (self.file, self.pageNr))
                    
                wxEndBusyCursor()
          
    def OnPrevPageButton(self, event):
        '''
        Invoked when user clicks the previous button.
        '''
        self.pageNr = self.pageNr - 1
        self.pdf.setCurrentPage(self.pageNr)
        self.sharedAppClient.SendEvent("position", (self.id, self.pageNr))
        self.sharedAppClient.SetData("position", (self.file, self.pageNr))

    def OnNextPageButton(self, event):
        '''
        Invoked when user clicks the next button.
        '''
        self.pageNr = self.pageNr + 1
        self.pdf.setCurrentPage(self.pageNr)
        self.sharedAppClient.SendEvent("position", (self.id, self.pageNr))
        self.sharedAppClient.SetData("position", (self.file, self.pageNr))

    def OnExit(self, event):
        '''
        Shut down shared pdf.
        '''
        self.sharedAppClient.Shutdown()
        
    #    
    # Callbacks for external events
    #

    def OpenCallback(self, event):
        '''
        Invoked when a open event is received.
        '''
        id, self.file, self.pageNr = event.data
        
        # Ignore my own events
        if self.id != id:
            wxBeginBusyCursor()
            wxCallAfter(self.pdf.LoadFile, self.file)
            wxCallAfter(self.pdf.setCurrentPage, self.pageNr)
            wxEndBusyCursor()
        
    def ChangePositionCallback(self, event):
        '''
        Invoked when a next event is received.
        '''
        id, self.pageNr = event.data
      
        # Ignore my own events
        if self.id != id:
            wxCallAfter(self.pdf.setCurrentPage, self.pageNr)        
               
    def __Layout(self):
        '''
        Layout of ui components.
        '''

        # Create UI objects
        self.openButton = wxButton(self, wxNewId(), "Open PDF File")
        self.prevButton = wxButton(self, wxNewId(), "<-- Previous Page")
        self.nextButton = wxButton(self, wxNewId(), "Next Page -->")
        
        sizer = wxBoxSizer(wxVERTICAL)
        btnSizer = wxBoxSizer(wxHORIZONTAL)
        
        sizer.Add(self.pdf, proportion=1, flag=wxEXPAND)

        btnSizer.Add(self.openButton, proportion=1, flag=wxEXPAND|wxALL, border=5)
        btnSizer.Add(self.prevButton, proportion=1, flag=wxEXPAND|wxALL, border=5)
        btnSizer.Add(self.nextButton, proportion=1, flag=wxEXPAND|wxALL, border=5)

        btnSizer.Add((50,-1), proportion=2, flag=wxEXPAND)
        sizer.Add(btnSizer, proportion=0, flag=wxEXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

#----------------------------------------------------------------------

class FileSelectorDialog(wxDialog):
    def __init__(self, parent, id, title, dataStoreClient):
        wxDialog.__init__(self, parent, id, title)

        # Create UI components.
        self.infoText = wxStaticText(self, -1, "Select pdf file to open: ",
                                     size = wxSize(300, 20), style=wxALIGN_LEFT)
        self.infoText2 = wxStaticText(self, -1, "File:")
        self.pdfList = wxComboBox(self, wxNewId(), size = wxSize(200, 20),
                                  choices = [], style=wxCB_DROPDOWN|wxCB_SORT)
        self.addFileButton = wxButton(self, wxNewId(), "Add File")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__Layout()

        EVT_BUTTON(self, self.addFileButton.GetId(), self.OpenFileDialog)
      
        # Create the data store client.
        self.dataStoreClient = dataStoreClient
        self.PopulateCombobox()
        
    def PopulateCombobox(self, default = None):
        # Get pdf files from venue
        fileNames = []

        wxBeginBusyCursor()
        try:
            self.dataStoreClient.LoadData()
            fileNames = self.dataStoreClient.QueryMatchingFiles("*.pdf")
        except:
            self.log.exception("FileSelectorDialog.PopulateCombobox: QueryMatchingFiles failed.")
        wxEndBusyCursor()
                
        self.pdfList.Clear()
        for file in fileNames:
            self.pdfList.Append(file)

        if default and not len(default) == 0:
            self.pdfList.SetValue(default)
        else:
            self.pdfList.SetSelection(0)

    def OpenFileDialog(self, event):
        dlg = wxFileDialog(self, wildcard="*.pdf")
        filePath = None
                
        if dlg.ShowModal() == wxID_OK:
            wxBeginBusyCursor()
            self.pageNr = 1
            filePath = dlg.GetPath()

            # Upload file to venue
         
            try:
                self.dataStoreClient.Upload(filePath)
            except:
                self.log.exception("OpenFileDialog: Upload file %s failed"%(filePath))

            self.PopulateCombobox(default = os.path.basename(filePath))
            wxEndBusyCursor()

        dlg.Destroy()
               
    def GetFile(self):
        return self.pdfList.GetValue()
                            
    def __Layout(self):
        # Create UI objects
        mainSizer = wxBoxSizer(wxVERTICAL)
        
        sizer = wxBoxSizer(wxVERTICAL)
        btnSizer1 = wxBoxSizer(wxHORIZONTAL)
        btnSizer = wxBoxSizer(wxHORIZONTAL)

        sizer.Add(wxSize(5,5))
        sizer.Add(self.infoText, 0, wxEXPAND|wxALL, 5)
        sizer.Add(wxSize(5,5))

        btnSizer1.Add(self.infoText2, 0, wxEXPAND|wxALL, 5)
        btnSizer1.Add(self.pdfList, 0, wxEXPAND|wxALL, 5)
        btnSizer1.Add(self.addFileButton, 0, wxEXPAND|wxALL, 5)
        sizer.Add(btnSizer1, 0, wxEXPAND, 10)
        
        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 10)
        
        btnSizer.Add(self.okButton, 1, wxRIGHT, 5)
        btnSizer.Add(self.cancelButton, 1)
        
        sizer.Add(btnSizer, 0, wxALIGN_CENTER)

        mainSizer.Add(sizer, 0, wxALL, 10)
        
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.SetAutoLayout(1)
        
#----------------------------------------------------------------------

def Usage():
    """
    How to use the program.
    """
    print "%s:" % sys.argv[0]
    print "    -a|--applicationURL : <url to application in venue>"
    print "    -v|--venueURL : <url to venue>"
    print "    -h|--help : print usage"
    print "    -d|--debug : print debugging output"
    
if __name__ == '__main__':
    # Get command line options
    initArgs = []
    appUrl = None
    venueUrl = None
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:d:v:h",
                                   ["applicationURL=","venueURL=",
                                    "debug", "help"])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)
        
    for o, a in opts:
        if o in ("-a", "--applicationURL"):
            appUrl = a
        elif o in ("-v", "--venueURL"):
            venueUrl = a
        elif o in ("-d", "--debug"):
            initArgs = ['--debug']
        elif o in ("-h", "--help"):
            Usage()
            sys.exit(0)

    if not appUrl:
        Usage()
        sys.exit(0)
                
    # Create the wx python application
    wxapp = wxPySimpleApp()
    wxBeginBusyCursor()
       
    # Inizialize AG application
    app = WXGUIApplication()
    name = "SharedPDF"
    app.Initialize(name, initArgs)

    if wxPlatform == '__WXMSW__':
        # Create the UI
        mainFrame = wxFrame(None, -1, name, size = wxSize(600, 600))
        viewer = PdfViewer(mainFrame, name, appUrl, venueUrl)

        # Start the UI main loop
        mainFrame.Show()
        wxEndBusyCursor()
           
        wxapp.MainLoop()

    else:
        wxEndBusyCursor()
        dlg = wxMessageDialog(frame, 'This application only works on MSW.',
                              'Sorry', wxOK | wxICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

  