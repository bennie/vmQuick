#!/usr/bin/env python2.7

# Some original code by Phillip Pollard used to build this
# Written by Shane Reed Aug-2015

from vmQuick import vmQuick
from argparse import ArgumentParser


def main():

    q = vmQuick('vcenter')

    parser = ArgumentParser()
    parser.add_argument('-v', '--vmname', dest='vm_name', help='vm to migrate')
    parser.add_argument('-H', '--host', dest='target_host', help='host to move to')
    parser.add_argument('-D', '--datastore', dest='target_datastore', help=' new datastore')
    args = parser.parse_args()

    if args.vm_name is None:
        vm_name = raw_input('Enter Name of vm: ')
    else:
        vm_name = args.vm_name

    if args.target_host is None:
        target_host = raw_input('Enter Name of target host: ')
    else:
        target_host = args.target_host

    if args.target_datastore is None:
        target_datastore = raw_input('Enter Name of target datastore: ')
    else:
        target_datastore = args.target_datastore

    print "Attempting to move {} to {} / {}".format(vm_name, target_host, target_datastore)

    task = q.vmotion_vm(vm_name, target_host, target_datastore)
    q.wait_for_tasks([task])

if __name__ == "__main__":
    main()
