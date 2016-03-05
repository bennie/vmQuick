import atexit
import getpass
import sys
import time
import re

# Allow self-signed SSL with pyVmomi

import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # monkey-patch to avoid HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

# End horrible security-removal code

from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect


class vmQuick:
    def __init__(self, server=None, username=None, password=None):
        self.content = None
        self.si = None
        if server:
            self.login(server, username, password)

    # Private Methods

    def _get_obj(self, vimtype, name, root=None):
        # Get the vsphere object associated with a given text name
        content = self._get_content()
        if not root:
            root = content.rootFolder

        container = content.viewManager.CreateContainerView(root, vimtype, True)
        for c in container.view:
            try:
                if c.name == name:
                    return c
            except vmodl.fault.ManagedObjectNotFound:
                # Managed object has been removed, is being created, etc. Skip it.
                pass
        return None

    def _get_all_objs(self, vimtype, root=None):
        # Get all vsphere objects associated with a given type
        content = self._get_content()
        if not root:
            root = content.rootFolder
        container = content.viewManager.CreateContainerView(root, vimtype, True)
        return {x: x.name for x in container.view}

    # Cache common references

    # CORRY: Consider using actual python "properties" here for getter/setter
    def _get_si(self):
        if not self.si:
            self.login()
        return self.si

    # CORRY: See last comment
    def _get_content(self):
        if not self.content:
            si = self._get_si()
            self.content = si.RetrieveContent()
        return self.content

    # Login method

    def login(self, server=None, username=None, password=None):
        """
        Conduct a console login
        """

        # CORRY: If this is a library, using input is really bad
        # CORRY: If for mixed use, detect TTY, except if no TTY
        if not username:
            sys.stderr.write(" Username: ")
            username = raw_input()
        if not password:
            password = getpass.getpass(prompt=" Password: ")

        self.si = SmartConnect(host=server, user=username, pwd=password, port=443)

        if not self.si:
            print "Couldn't connect to vCenter using specified username and password"
            # CORRY: Again, for library use, sys.exit is really bad, as it will pop the exception stack
            sys.exit(1)

        # CORRY: Consider using context manager instead, if library (look for python "with" statment
        atexit.register(Disconnect, self.si)
        # CORRY: Returning the self is really strange, I would not bother
        return self

    # General methods

    def get_cluster_by_name(self, name, root=None):
        """
        Find a cluster by it's name and return it
        """
        # CORRY: Why is the caller required to wrap in a list[] if everyone passes a single item?
        return self._get_obj([vim.ClusterComputeResource], name, root)

    def get_clusters(self, root=None):
        """
        Returns all clusters
        """
        return self._get_all_objs([vim.ClusterComputeResource], root)

    def get_datacenter_by_name(self, name, root=None):
        """
        Find a datacenter by it's name and return it
        """
        return self._get_obj([vim.Datacenter], name, root)

    def get_datacenters(self, root=None):
        """
        Returns all datacenters
        """
        return self._get_all_objs([vim.Datacenter], root)

    def get_datastore_by_name(self, name, root=None):
        """
        Find a datastore by it's name and return it
        """
        return self._get_obj([vim.Datastore], name, root)

    def get_datastores(self, root=None):
        """
        Returns all datastores
        """
        return self._get_all_objs([vim.Datastore], root)

    def get_dvs_network_by_name(self, name, root=None):
        """
        Find a distributed virtual switch network by it's name and return it
        """
        return self._get_obj([vim.dvs.DistributedVirtualPortgroup], name, root)

    def get_folder_by_name(self, name, root=None):
        """
        Find a folder by it's name and return it
        """
        return self._get_obj([vim.Folder], name, root)

    def get_folders(self, root=None):
        """
        Returns all datastores
        """
        return self._get_all_objs([vim.Folder], root)

    def get_host_by_name(self, name, root=None):
        """
        Find a virtual machine by it's name and return it
        """
        return self._get_obj([vim.HostSystem], name, root)

    def get_hosts(self, root=None):
        """
        Returns all hosts
        """
        raw_hosts = self._get_all_objs([vim.HostSystem], root)
        return sorted(raw_hosts, key=lambda host: host.name)

    def get_hosts_in_cluster(self, cluster_regex, root=None):
        """
        Returns all hosts from a cluster. Regex should be like this
        '^Tier 4' to see all Tier 4 clusters
        """
        hosts = []
        # Get the clusters
        clusters = self._get_all_objs([vim.ClusterComputeResource], root)
        for cluster in sorted(clusters, key=lambda cluster: cluster.name):
            if re.search(cluster_regex, cluster.name, re.I):
                for h in cluster.host:
                    assert type(h) == vim.HostSystem
                    hosts.append(h)

        return hosts

    def get_simple_network_by_name(self, name, root=None):
        """
        Find a simple-switch virtual network by it's name and return it
        """
        return self._get_obj([vim.Network], name, root)

    def get_vm_by_name(self, name, root=None):
        """
        Find a virtual machine by it's name and return it
        """
        return self._get_obj([vim.VirtualMachine], name, root)

    def get_vms(self, root=None):
        """
        Returns all vms
        """
        raw_vms = self._get_all_objs([vim.VirtualMachine], root)
        return sorted(raw_vms, key=lambda vm: vm.summary.config.name)

    def get_resource_pool_by_name(self, name, root=None):
        """
        Find a virtual machine by it's name and return it
        """
        return self._get_obj([vim.ResourcePool], name, root)

    def get_resource_pools(self, root=None):
        """
        Returns all resource pools
        """
        return self._get_all_objs([vim.ResourcePool], root)

    def is_ready(vm):
        while True:
            system_ready = vm.guest.guestOperationsReady
            system_state = vm.guest.guestState
            system_uptime = vm.summary.quickStats.uptimeSeconds
            if system_ready and system_state == 'running' and system_uptime > 90:
                break
            time.sleep(10)
            # CORRY: Consider a maximum wait time, throw exception

    def login_in_guest(username, password):
        return vim.vm.guest.NamePasswordAuthentication(username=username, password=password)

    def start_process(si, vm, auth, program_path, args=None, env=None, cwd=None):
        cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args, programPath=program_path, envVariables=env, workingDirectory=cwd)
        cmdpid = si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=auth, spec=cmdspec)
        return cmdpid

    def storage_vmotion_vm(self, vm_name, host_name, storage_name):
        vm = self.get_vm_by_name(vm_name)
        host = self.get_host_by_name(host_name)

        ds = None
        for candidate in host.datastore:
            if candidate.name == storage_name:
                ds = candidate
                break

        if ds is None:
            print "Can't find volume {} on host {}".fomat(storage_name, host.name)
            sys.exit(1)

        relocate_spec = vim.vm.RelocateSpec()
        relocate_spec.datastore = ds

        return vm.Relocate(relocate_spec)

    def vmotion_vm(self, vm_name, host_name, storage_name):
        vm = self.get_vm_by_name(vm_name)
        host = self.get_host_by_name(host_name)

        assert host is not None
        ds = None

        for candidate in host.datastore:
            if candidate.name == storage_name:
                ds = candidate
                break

        if ds is None:
            print "Can't find volume {} on host {}".fomat(storage_name, host.name)
            sys.exit(1)

        relocate_spec = vim.vm.RelocateSpec(host=host)
        relocate_spec.datastore = ds
        # relocate_spec.host = host

        return vm.Relocate(relocate_spec)

    def wait_for_tasks(self, tasks):
        """
        Given a list of tasks, this method blocks until all tasks are complete
        """
        si = self._get_si()
        pc = si.content.propertyCollector

        taskList = [str(task) for task in tasks]

        # Create filter
        objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task) for task in tasks]
        propSpec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task, pathSet=[], all=True)
        filterSpec = vmodl.query.PropertyCollector.FilterSpec()
        filterSpec.objectSet = objSpecs
        filterSpec.propSet = [propSpec]

        filterRef = pc.CreateFilter(filterSpec, True)

        try:
            version, state = None, None

            # Loop looking for updates till the state moves to a completed state.
            while len(taskList):
                update = pc.WaitForUpdates(version)
                for filterSet in update.filterSet:
                    for objSet in filterSet.objectSet:
                        task = objSet.obj
                        for change in objSet.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue

                            if not str(task) in taskList:
                                continue

                            if state == vim.TaskInfo.State.success:
                                # Remove task from taskList
                                taskList.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                raise task.info.error
                            # Move to next version
                            version = update.version
        finally:
            if filterRef:
                filterRef.Destroy()
