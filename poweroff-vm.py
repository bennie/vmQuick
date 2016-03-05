#!/usr/bin/env python2.7

import click
from vmQuick import vmQuick

@click.command()
@click.option('--vmuser', prompt='VMware Username', help='VMware username to perform the actions with.')
@click.option('--vmpass', prompt='VMware Password', help='Password for the given VMware username.', hide_input=True)
@click.option('--vmname', help='VM to poweroff.')
def main(vmuser, vmpass, vmname):
    q = vmQuick('vcenter', vmuser, vmpass)
    vm = q.get_vm_by_name(vmname)
    task = vm.PowerOff()
    q.wait_for_tasks([task])

if __name__ == '__main__':
    main()