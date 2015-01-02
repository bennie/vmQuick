#!/usr/bin/env python2.7
"""list-hosts.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-hosts.py

"""

import vmutils

si = vmutils.login('vcenter','MYUSERNAME','MYPASSWORD')
hosts = vmutils.get_hosts(si)

print "vCenter\tHost\tVersion\tRuntime Status\tMGMT IP\tsubnet\tMAC"

for host in hosts:
    ipaddr = ''
    subnet = ''

    for config in host.config.virtualNicManagerInfo.netConfig:
        if config.nicType == 'management':
            key = str(config.selectedVnic[0])
            for vnic in config.candidateVnic:
                if vnic.key == key: 
                    ipaddr = vnic.spec.ip.ipAddress
                    subnet = vnic.spec.ip.subnetMask
                    mac    = vnic.spec.mac

    print "\t".join(['vcenter',host.name,host.config.product.version,host.runtime.connectionState,ipaddr,subnet,mac])
