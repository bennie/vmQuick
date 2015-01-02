#!/usr/bin/env python2.7

from vmQuick import vmQuick
import getopt, sys

if len(sys.argv) < 3:
	sys.exit("Usage: ./vmotion.py USERNAME PASSWORD TARGET_HOST TARGET_VOLUME VM_NAME")

vms = sys.argv
vms.pop(0) # lose the name of the script
username = vms.pop(0)
password = vms.pop(0)
target_host = vms.pop(0)
target_vol  = vms.pop(0)

q = vmQuick('vcenter.myserver.com')

for vm_name in vms:
   print "Moving {} to {} / {}".format(vm_name,target_host,target_vol)
   task = q.vmotion_vm(vm_name,target_host,target_vol)
   q.wait_for_tasks([task])
