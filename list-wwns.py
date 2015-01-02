#!/usr/bin/env python2.7
"""list-wwns.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-wwns.py

"""

import pyVmomi, re, vmutils

si = vmutils.login('vcenter','MYUSERNAME','MYPASSWORD')
hosts = vmutils.get_hosts(si)

### Subs

def wwnHex(raw):
    out = ''
    for chunk in re.findall('..', "%x" % raw ):
        if len(out) > 1:
            out += ':'
        out += chunk
    return out

### Gather the data

print "Host\tvCenter\tPCI Address\tDevice\tStatus\tModel\tDriver\tPWWN\tNWWN"

for host in sorted(hosts,key=lambda host: host.name):
    if host.runtime.connectionState != "connected":
        continue

    for hba in host.config.storageDevice.hostBusAdapter:
        if type(hba) == pyVmomi.types.vim.host.FibreChannelHba:
            print "\t".join([host.name,'vcenter',hba.pci,hba.device,hba.status,hba.model,hba.driver,wwnHex(hba.portWorldWideName),wwnHex(hba.nodeWorldWideName)])
