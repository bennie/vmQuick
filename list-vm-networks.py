#!/usr/bin/env python2.7
"""list-vm-networks.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vm-networks.py

"""

import vmquick

si = vmquick.login('vcenter','MYUSERNAME','MYPASSWORD')
vms = vmquick.get_registered_vms(si)

### Gather the data

print "Guest\thost\tNetwork Label"

for vm in vms:
    for net in vm.network:
    	print "\t".join([vm.summary.config.name,vm.summary.runtime.host.name,net.name])
