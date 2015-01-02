#!/usr/bin/env python2.7
"""list-vms.py

Author: 
        Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vms.py

"""

import vmquick

si = vmquick.login('vcenter','MYUSERNAME','MYPASSWORD')
folders = vmquick.get_folders(si)

### Gather the data


#print "Guest\tIP\tPath\tvcenter\thost\tOS"

for folder in folders:
	if folder.childType[1] == "VirtualMachine":
		print folder.name
