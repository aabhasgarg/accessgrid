#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.27 2003-08-21 23:27:11 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import mailcap
import string

try:
    import _winreg
    from AccessGrid.Platform import Win32RegisterMimeType
except:
    pass

#from wxPython.wx import wxTheMimeTypesManager as mtm
from wxPython.wx import wxFileTypeInfo
from wxPython.lib.throbber import Throbber
from wxPython.wx import *
from wxPython.lib.imagebrowser import *
from AccessGrid import icons

from AccessGrid.Utilities import SubmitBug
from AccessGrid.Utilities import formatExceptionInfo
from Toolkit import GetVersion


class MessageDialog:
    def __init__(self, frame, text, text2 = "", style = wxOK|wxICON_INFORMATION):
        messageDialog = wxMessageDialog(frame, text, text2, style)
        messageDialog.ShowModal()
        messageDialog.Destroy()
      
class ErrorDialog:
    def __init__(self, frame, text, text2 = "", style =  wxICON_ERROR |wxYES_NO | wxNO_DEFAULT):
        info = text + "\n\nDo you wish to send an automated error report?"
        errorDialog = wxMessageDialog(frame, info, text2, wxICON_ERROR |wxYES_NO | wxNO_DEFAULT)
        
        if(errorDialog.ShowModal() == wxID_YES):
            # The user wants to send an error report
            bugReportCommentDialog = BugReportCommentDialog(frame)

            if(bugReportCommentDialog.ShowModal() == wxID_OK):
                # Submit the error report to Bugzilla
              
                SubmitBug(bugReportCommentDialog.GetComment())
                bugFeedbackDialog = wxMessageDialog(frame, "Your error report has been sent, thank you.",
                                                    "Error Reported", style = wxOK|wxICON_INFORMATION)
                bugFeedbackDialog.ShowModal()
                bugFeedbackDialog.Destroy()       

            bugReportCommentDialog.Destroy()
            errorDialog.Destroy()


class BugReportCommentDialog(wxDialog):
    def __init__(self, parent):
        wxDialog.__init__(self, parent, -1, "Comment for Bug Report")
        self.text = wxStaticText(self, -1, "Please, enter a description of the problem you are experiencing.", style=wxALIGN_LEFT)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.commentBox = wxTextCtrl(self, -1, "", size = wxSize(300,100), style = wxTE_MULTILINE)
        self.line = wxStaticLine(self, -1)
        self.Centre()
        self.Layout()
        
    def GetComment(self):
        return self.commentBox.GetValue()

    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.text, 0, wxALL, 10)
        sizer.Add(self.commentBox, 0, wxALL | wxEXPAND, 10)
        sizer.Add(self.line, 0, wxALL | wxEXPAND, 10)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 5)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER | wxBOTTOM, 5) 
            
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
class ErrorDialogWithTraceback:
    def __init__(self, frame, text, text2 = "", style = wxOK | wxICON_ERROR):
        
       (name, args, traceback_string_list) = formatExceptionInfo()

       tbstr = ""
       for x in traceback_string_list:
           print(x)
           tbstr += x + "\n"

       print sys.exc_type
       print sys.exc_value
       info = text + "\n\n"+"Type: "+str(sys.exc_type)+"\n"+"Value: "+str(sys.exc_value) + "\nTraceback:\n" + tbstr
       errorDialog = wxMessageDialog(frame, info, text2, style)
       errorDialog.ShowModal()
       errorDialog.Destroy()
        

class ProgressDialog(wxProgressDialog):
    count = 1

    def __init__(self, title, message, maximum):
        wxProgressDialog.__init__(self, title, message, maximum, style = wxPD_AUTO_HIDE| wxPD_APP_MODAL)
            
    def UpdateOneStep(self):
        self.Update(self.count)
        self.count = self.count + 1

class AboutDialog(wxDialog):
    version = GetVersion().AsString()
        
    def __init__(self, parent):
        wxDialog.__init__(self, parent, -1, self.version)
        self.panel = wxPanel(self, -1)
                
        bmp = icons.getAboutBitmap()

        info = "Version: %s \nCopyright@2001-2003 by University of Chicago, \nAll rights reserved\nPlease visit www.accessgrid.org for more information" %self.version
        self.SetSize(wxSize(bmp.GetWidth(),bmp.GetHeight()))
        self.panel.SetSize(wxSize(bmp.GetWidth(),bmp.GetHeight()))
        self.image = wxStaticBitmap(self.panel, -1, bmp, size = wxSize(bmp.GetWidth(), bmp.GetHeight()))
        self.text = wxStaticText(self.panel, -1, info, pos = wxPoint(80,100))
        self.Layout()
                            
    #def ProcessLeftDown(self, evt):
    #    self.Hide()
    #    return false

class AppSplash(wxSplashScreen):
    def __init__(self):
        bmp = icons.getAboutBitmap()
        
        wxSplashScreen.__init__(self, bmp,
                                wxSPLASH_CENTRE_ON_SCREEN|
                                wxSPLASH_NO_TIMEOUT , 4000, None,
                                -1, style=wxSIMPLE_BORDER|
                                wxFRAME_NO_TASKBAR
                                |wxSTAY_ON_TOP)

        self.info = wxStaticText(self, -1, "Loading Venue Client.")
        self.__layout()
        EVT_CLOSE(self, self.OnClose)

    def __layout(self):
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.info)
        
        self.SetAutoLayout(1)
        self.SetSizer(box)
        self.Layout()
                
    def OnClose(self, evt):
        evt.Skip()
    
# def GetMimeCommands(filename = None, type = None, ext = None):
#      """
#      This function returns anything in the local mime type database for the
#      type or extension specified.
#      """
#      cdict = dict()
    
#      if type != None:
#          fileType = mtm.GetFileTypeFromMimeType(type)
#      elif ext != None:
#          fileType = mtm.GetFileTypeFromExtension(ext)

#      if fileType != None and filename != None:
#          mimeType = fileType.GetMimeType()
#          if mimeType != None:
#              cmds = fileType.GetAllCommands(filename, mimeType)
#              if None == cmds:
#                  verbs = []
#                  cmdlines = []
#              else:
#                  verbs, cmdlines = cmds
#              for i in range(0, len(verbs)):
#                  cdict[string.lower(verbs[i])] = cmdlines[i]
#          else:
#              cdict = None
#      else:
#          cdict = None

#      return cdict

def ProgressDialogTest():
    max = 100
     
    dlg = ProgressDialog("Start up", "Loading Venue Client. Please be patient.", max)
    dlg.Show()
  
    keepGoing = True
    count = 0
    while keepGoing and count < max:
        count = count + 1
        wxSleep(1)

        if count == max / 2:
            keepGoing = dlg.Update(count, "Half-time!")
        else:
            keepGoing = dlg.Update(count)

    dlg.Destroy()

def AboutDialogTest():
    dlg = AboutDialog(None)
    dlg.ShowModal()
    dlg.Destroy()
   
if __name__ == "__main__":
    app = wxPySimpleApp()

    #ProgressDialogTest()
    AboutDialogTest()

    app.MainLoop()
    
