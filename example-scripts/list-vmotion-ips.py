#!/usr/bin/env python2.7
"""vmotion-ips.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vmotion-ips.py

"""
from vmQuick import vmQuick

q = vmQuick('vcenter.myserver.com','MYUSERNAME','MYPASSWORD')
hosts = q.get_hosts()

### Gather the data

print "vCenter\tHost\tIP\tsubnet"

for host in hosts:
    ipaddr = ''
    subnet = ''
    if host.config.vmotion.ipConfig:
        ipaddr = host.config.vmotion.ipConfig.ipAddress
        subnet = host.config.vmotion.ipConfig.subnetMask

    print "\t".join(['vcenter',host.name,ipaddr,subnet])
