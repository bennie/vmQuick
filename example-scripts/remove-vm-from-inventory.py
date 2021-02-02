#!/usr/bin/env python2.7

from vmQuick import vmQuick
import sys

q = vmQuick('vcenter')

vmlist = sys.argv
vmlist.pop(0)

for vm_name in vmlist:
    vm = q.get_vm_by_name(vm_name)

    print "Removing: {} / {}".format(vm_name, vm.datastore[0].name)

    if hasattr(vm, 'summary') and vm.summary.runtime.powerState == 'poweredOn':
        task = vm.PowerOff()
        q.wait_for_tasks([task])

    vm.UnregisterVM()
