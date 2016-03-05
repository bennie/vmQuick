#!/usr/bin/env python2.7
"""list-snapshots.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    list-snapshots.py

"""

from vmQuick import vmQuick

q = vmQuick('vcenter.myserver.com','MYUSERNAME','MYPASSWORD')
vms = q.get_vms()

def print_snap_info(vmname,ref):
    for snap in ref:
    	desc = snap.description.replace('\n',';')
        print "\t".join([vmname,str(snap.createTime),str(snap.id),snap.name,desc])
        if snap.childSnapshotList:
            print_snap_info(vmname,snap.childSnapshotList)

print "VM\tCreated\tSnapshot ID\tSnapshot Name\tSnapshot Description"

for vm in vms:
    if hasattr(vm, 'snapshot') and vm.snapshot != None:
        print_snap_info(vm.summary.config.name,vm.snapshot.rootSnapshotList)
