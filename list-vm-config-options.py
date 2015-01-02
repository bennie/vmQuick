#!/usr/bin/env python

from pyVmomi import vim
import vmutils

si = vmutils.login('vcenter')
vm = vmutils.get_vm_by_name(si,'lpm17 - Delete Dec 31')

for config in vm.config.extraConfig:
	if config.key != 'guestinfo.hostname':
		continue
	print config

optval = vim.option.OptionValue()
optval.key = 'guestinfo.hostname'
optval.value = 'beau'

vmspec = vim.vm.ConfigSpec()
vmspec.extraConfig.append(optval)

task = vm.Reconfigure(vmspec)

vmutils.wait_for_tasks(si,[task])

for config in vm.config.extraConfig:
	if config.key != 'guestinfo.hostname':
		continue
	print config
