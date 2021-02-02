#!/usr/bin/env python2.7

from pyVmomi import vim
from vmQuick import vmQuick

q = vmQuick('vcenter')

vm = q.get_vm_by_name('lpm17 - Delete Dec 31')

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

q.wait_for_tasks([task])

for config in vm.config.extraConfig:
    if config.key != 'guestinfo.hostname':
        continue
    print config