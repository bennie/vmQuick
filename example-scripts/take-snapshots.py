#!/usr/bin/env python2.7
"""take-snapshots.py

Author: Phillip Pollard <phillip@purestorage.com>

Usage:
    take-snapshots.py

"""

from vmQuick import vmQuick
q = vmQuick('vcenter') # shell will prompt for login

vms_to_snap = "pxe43 pxe44 pxe45 pxe46 pxe47".split()
snapshot_name = "after-puppet"
snapshot_description = "Snapshot before bootstrapping puppet."
include_memory = False
quiesce_disk   = True

tasks = []

for name in vms_to_snap:
    print "Snapshotting {}".format(name)
    vm = q.get_vm_by_name(name)
    task = vm.CreateSnapshot(snapshot_name,snapshot_description,include_memory,quiesce_disk)
    tasks.append(task)
    if len(tasks) > 3:
        print "Waiting on tasks..."
        q.wait_for_tasks(tasks)
        tasks = []

if len(tasks) > 0:
    print "Waiting on tasks..."
    q.wait_for_tasks(tasks)

print "Done"