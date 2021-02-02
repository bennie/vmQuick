#!/usr/bin/env python2.7
"""list-vm-networks.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vm-networks.py

"""

from vmQuick import vmQuick

q = vmQuick('vcenter.myserver.com','MYUSERNAME','MYPASSWORD')
vms = q.get_vms()

### Gather the data

print "Guest\thost\tNetwork Label"

for vm in vms:
    for net in vm.network:
        print "\t".join([vm.summary.config.name,vm.summary.runtime.host.name,net.name])