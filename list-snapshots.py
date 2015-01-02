#!/usr/bin/env python2.7
"""list-snapshots.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-snapshots.py

"""

import vmutils

si = vmutils.login('vcenter','MYUSERNAME','MYPASSWORD')
vms = vmutils.get_registered_vms(si)

def print_snap_info(vmname,ref):
	for snap in ref:
		print "\t".join([vmname,str(snap.createTime),str(snap.id),snap.name,snap.description])
		if snap.childSnapshotList:
			print_snap_info(vmname,snap.childSnapshotList)

print "VM\tCreated\tSnapshot ID\tSnapshot Name\tSnapshot Description"

for vm in vms:
	if (vm.snapshot):
		print_snap_info(vm.summary.config.name,vm.snapshot.rootSnapshotList)
