#
# The following are variables that are used throughout the rest of the
# spec file. If you see %{variable_name} this is where it's assigned
#
%define	name		AccessGrid
%define version		2.2
%define release		4
%define	prefix		/usr
%define sysconfdir	/etc/%{name}/Config
%define sharedir	%{prefix}/share
%define gnomedir	%{sharedir}/gnome/apps
%define kdedir		%{sharedir}/applnk
%define buildroot	/usr/src/redhat/BUILD/AccessGrid-2.2

#
# The following defines the AccessGrid rpm
# Required: pyGlobus rpm installed
# Required: logging rpm installed
# Obsoletes: AccessGrid-2.0alpha
#

Summary:	The Access Grid Toolkit
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	AGTPL
Group:		Utilities/System
URL:		http://www.accessgrid.org
Vendor:		Argonne National Laboratory
Source:		%{name}-%{version}.tar.gz
BuildRoot:	%{buildroot}
Requires:	wxPythonGTK-py2.2
Requires:	globus-accessgrid
Requires:	glibc >= 2.2.5-43
Obsoletes:	AccessGrid-2.0alpha
Obsoletes:	AccessGrid-2.0beta
Obsoletes:	AccessGrid-BridgeServer
Obsoletes:	AccessGrid-VenueServer
Obsoletes:	AccessGrid-VenueClient
Obsoletes:	AccessGrid-rat
Obsoletes:	AccessGrid-vic
Obsoletes:	pyOpenSSL_AG
Obsoletes:	pyGlobus


%description
The Access Grid Toolkit provides the necessary components for users to participate in Access Grid based collaborations, and also for developers to work on network services, applications services and node services to extend the functionality of the Access Grid.

This module provides the core components to start participating in the Access Grid.

%prep
%setup -n AccessGrid-%{version} -c

#
# The following builds the package using setup.py
# It starts by zipping up the services in the services directory
# then builds the package
#

%build
echo %{pyver}

#
# The following installs the package in the buildroot,
# moves the etc directory to the "root" directory,
# until services are starting at boot
#

%install
# Move node services and shared apps into etc 
mv NodeServices etc/AccessGrid/Config
mv SharedApplications etc/AccessGrid/Config
mkdir etc/AccessGrid/Config/Services
mkdir etc/AccessGrid/Config/PackageCache
mkdir etc/AccessGrid/Config/Logs



# Create a usr dir, and move dirs thereunder
mkdir usr
mv share usr/share
mv lib usr/lib
mv bin usr/bin


#
# Define the files that are to go into the AccessGrid package
# - Mark documents as documents for rpm
# - Install python modules with default permissions
# - Install AGServiceManager.py and agsm service with executable permissions
#
%files
%defattr(-,root,root)
%{prefix}/lib
/etc/AccessGrid
%{sharedir}/%{name}/ag.ico
%defattr(0755,root,root)
%{prefix}/bin/AGServiceManager.py
# - Install AGNodeService.py, VenueClient.py, and NodeManagement.py with
#   executable permissions
# - Install the AGNodeService config file and tag it as a config file
#   for rpm
# - Install the default node configuration, make it owned by ag, and tag it
#   as a config file for rpm
%defattr(0755,root,root)
%{prefix}/bin/AGNodeService.py
%{prefix}/bin/VenueClient.py
%{prefix}/bin/NodeManagement.py
%{prefix}/bin/NodeSetupWizard.py
%{prefix}/bin/CertificateRequestTool.py
%{prefix}/bin/certmgr.py
%{prefix}/bin/agpm.py
%{sharedir}/doc/AccessGrid
%defattr(-,root,root)
#
# - Install VenueManagement.py and VenueServer.py
#   with executable permissions
#
%defattr(0755,root,root)
%{prefix}/bin/VenueManagement.py
%{prefix}/bin/VenueServer.py
#
# - Install the python BridgeServer implementation
# - Install the QuickBridge executable
#
%defattr(0755,root,root)
%{prefix}/bin/BridgeServer.py
%{prefix}/bin/QuickBridge
# - Install the GNOME and KDE menu items
%{gnomedir}/%{name}
%{kdedir}/%{name}

# Temporarily include vic to support SetupVideo.py
#%{prefix}/bin/vic

#
# AccessGrid package postinstall commands
# - Make a file, /tmp/AccessGrid-Postinstall.py, run it, then delete.
#   This script will compile all the AccessGrid python modules
#

%post
cat <<EOF > /tmp/AccessGrid-Postinstall.py
#!/usr/bin/python2
import AccessGrid
import AccessGrid.hosting
import os
import os.path
import glob
import sys

def modimport(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.py")):
	try:
            __import__(module.__name__ + "." + os.path.basename(module_file[:-3]))
	except:
	    pass

sys.stdout.write("Compiling Access Grid Python modules.... ")
modimport(AccessGrid)
modimport(AccessGrid.hosting)
modimport(AccessGrid.Platform)
sys.stdout.write("Done\n")
EOF
. /etc/profile.d/globus.sh
chmod +x /tmp/AccessGrid-Postinstall.py
/tmp/AccessGrid-Postinstall.py
rm -f /tmp/AccessGrid-Postinstall.py
agpm.py --post-install

#
# AccessGrid package pre-uninstall
# - Create a file, /tmp/AccessGrid-Preuninstall.py, run it, then delete it.
#   This script will remove those compiled AccessGrid python modules

%preun
cat <<EOF > /tmp/AccessGrid-Preuninstall.py
#!/usr/bin/python2
import AccessGrid
import AccessGrid.hosting
import os
import os.path
import glob

def delcompiled(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.pyc")):
        try:
            os.remove(module_file)
        except os.error:
            pass

delcompiled(AccessGrid.hosting.SOAPpy)
delcompiled(AccessGrid.hosting.Security)
delcompiled(AccessGrid.hosting.Platform)
delcompiled(AccessGrid.hosting)
delcompiled(AccessGrid)
EOF
. /etc/profile.d/globus.sh
chmod +x /tmp/AccessGrid-Preuninstall.py
/tmp/AccessGrid-Preuninstall.py
rm -f /tmp/AccessGrid-Preuninstall.py

#
# After the RPMs have been successfully built remove the temporary build
# space
#

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

#
# This is the ChangeLog. You should add to this if you do anything to this
# spec file
#

%changelog

* Fri May 16 2003 Ti Leggett <leggett@mcs.anl.gov>
- Fixed the ag user add problems (hopefully)
- Added MailcapSetup.py to the AccessGrid package

* Wed Mar 26 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added a plethora of comments
- Fixed a few permissions for some install files
- Now removes the AccessGrid pre-uninstall script after it's run

* Thu Mar 13 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added user and group creation in preinstall
- Added postinstall to compile python modules
- Services are added to chkconfig for starting
- Added preuninstall to remove compiled modules
- Move etc and var down a dir after python install so they're where they need to be

* Fri Feb 21 2003 Ti Leggett <leggett@mcs.anl.gov>
- Fixed where docs go
- Added default node configuration file

* Fri Feb 14 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added postinstall for VenueClient to create AGNodeService config file

* Thu Feb 13 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added SetupVideo.py to VideoProducer

* Fri Feb 06 2003 Ti Leggett <leggett@mcs.anl.gov>
- Modularized the RPMs

* Tue Feb 05 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created

