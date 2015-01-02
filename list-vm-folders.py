#!/usr/bin/env python2.7
"""list-vms.py

Author: 
        Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vms.py

"""

from vmQuick import vmQuick

q = vmQuick('vcenter.myserver.com','MYUSERNAME','MYPASSWORD')
folders = q.get_folders()

### Gather the data


#print "Guest\tIP\tPath\tvcenter\thost\tOS"

for folder in folders:
	if folder.childType[1] == "VirtualMachine":
		print folder.name
