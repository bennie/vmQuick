#!/usr/bin/env python2.7
"""list-vms.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vms.py

"""

import pyVmomi, vmquick

si = vmquick.login('vcenter','MYUSERNAME','MYPASSWORD')
vms = vmquick.get_registered_vms(si)

print "VM\thost\tvCenter\tMAC\tlabel\tnetwork\tstatus"

for vm in vms:
    for device in vm.config.hardware.device:
        if type(device.backing) == pyVmomi.types.vim.vm.device.VirtualEthernetCard.NetworkBackingInfo:
            print "\t".join([vm.config.name,vm.summary.runtime.host.name,'vcenter',device.macAddress,device.deviceInfo.label,device.backing.deviceName,str(device.connectable.connected)])
