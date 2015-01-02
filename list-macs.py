#!/usr/bin/env python2.7
"""list-macs.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-macs.py

"""

from vmQuick import vmQuick
from pyVmomi import vim

q = vmQuick('vcenter.myserver.com','MYUSERNAME','MYPASSWORD')
vms = q.get_vms()

print "VM\thost\tvCenter\tMAC\tlabel\tnetwork\tstatus"

for vm in vms:
    for device in vm.config.hardware.device:
        if type(device.backing) == vim.vm.device.VirtualEthernetCard.NetworkBackingInfo:
            print "\t".join([vm.config.name,vm.summary.runtime.host.name,'vcenter',device.macAddress,device.deviceInfo.label,device.backing.deviceName,str(device.connectable.connected)])
