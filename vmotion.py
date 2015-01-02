#!/usr/bin/env python2.7

import getopt, sys, vmquick

if len(sys.argv) < 3:
	sys.exit("Usage: ./vmotion.py USERNAME PASSWORD TARGET_HOST TARGET_VOLUME VM_NAME")

vms = sys.argv
vms.pop(0) # lose the name of the script
username = vms.pop(0)
password = vms.pop(0)
target_host = vms.pop(0)
target_vol  = vms.pop(0)

si = vmquick.login('vcenter',username,password)

for vm_name in vms:
   print "Moving {} to {} / {}".format(vm_name,target_host,target_vol)
   task = vmquick.vmotion_vm(si,vm_name,target_host,target_vol)
   vmquick.wait_for_tasks(si,[task])
