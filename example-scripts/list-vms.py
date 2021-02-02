#!/usr/bin/env python2.7
"""list-vms.py

Author:
        Phillip Pollard <phillip@purestorage.com>

Usage:
    list-vms.py

"""

import time
import pprint

from vmQuick import vmQuick

q = vmQuick('vcenter.myserver.com','MYUSERNAME','MYPASSWORD')

### We could loop over get_vms() - 
# vms = q.get_vms()
# for vm in vms:

### Gather the data with cluster info

clusters = q.get_clusters()

print "Cluster\tGuest\tIP\thost\tPath\tOS\tCreated"

for clus in sorted(clusters.keys()):
    for vm in sorted(clus.resourcePool.vm, key=lambda vm: vm.summary.runtime.host.name):

        os = ''
        if vm.summary.config.guestFullName: os = vm.summary.config.guestFullName

        ip = ''
        if vm.summary.guest.ipAddress: ip = vm.summary.guest.ipAddress

        host = ''
        if vm.summary.runtime.host: host = vm.summary.runtime.host.name

        created = ''
        for config in vm.config.extraConfig:
            if config.key == 'guestinfo.created':
                t = time.localtime(int(config.value))
                created = "{} ({})".format(time.strftime("%d %b %Y %H:%M:%S",t),config.value)

        print "\t".join([clusters[clus],vm.summary.config.name,ip,host,vm.summary.config.vmPathName,os,created])
