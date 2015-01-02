#!/usr/bin/env python2.7
"""list-vms.py

Author: 
        Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vms.py

"""

import vmutils

si = vmutils.login('vcenter','MYUSERNAME','MYPASSWORD')
vms = vmutils.get_registered_vms(si)

### Gather the data

print "Guest\tIP\tPath\tvcenter\thost\tOS"

for vm in vms:
    os = ''
    if vm.summary.config.guestFullName: os = vm.summary.config.guestFullName
    ip = ''
    if vm.summary.guest.ipAddress: ip = vm.summary.guest.ipAddress
    print "\t".join([vm.summary.config.name,ip,vm.summary.config.vmPathName,'vcenter',vm.summary.runtime.host.name,os])
