#!/usr/bin/env python2.7
"""list-hosts.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-hosts.py

"""

from vmQuick import vmQuick

q = vmQuick('vcenter.myserver.com','MYUSERNAME','MYPASSWORD')
hosts = q.get_hosts()

print "vCenter\tHost\tVersion\tRuntime Status\tMGMT IP\tsubnet\tMAC\tMax EVC\tCurrent EVC"

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

    max      = host.summary.maxEVCModeKey
    current  = host.summary.currentEVCModeKey

    if not current:
        current = "[NOT SET]"

    print "\t".join(['vcenter',host.name,host.config.product.version,host.runtime.connectionState,ipaddr,subnet,mac,max,current])
