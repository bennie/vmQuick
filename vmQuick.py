from collections import deque
try:
    # Python 3.3+
    from contextlib import ExitStack
except ImportError:
    # Py2
    from contextlib2 import ExitStack
import getpass
import pprint
import sys
import time
import re
import warnings

from pyVmomi import vim, vmodl

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

from pyVim.connect import SmartConnection

# python 2/3 compatibility hack
try:
    input = raw_input
except NameError:
    pass


class vmQuick:
    def __init__(self, server=None, username=None, password=None):
        self.content = None
        self.si = None
        self._resources = ExitStack()
        if server:
            self.login(server, username, password)

    def __enter__(self):
        self._resources.__enter__()
        return self

    def __exit__(self, *exc):
        self._resources.__exit__(*exc)

    def __del__(self):
        self._resources.close()

    # Private Methods

    def _find_vm_by_name(self, name):
        """
        Finds a virtual machine by its name and returns it.
        This performs recursive FindChild index operations to avoid
        a brute force scan.
        """
        content = self._get_content()
        entities = deque(content.rootFolder.childEntity)
        while entities:
            # FindChild only searches for immediate children of a managed
            # entity.  Perform a recursive search over all groups, which
            # should still be faster than iterating over all entities.
            entity = entities.popleft()
            if isinstance(entity, vim.Datacenter):
                entity = entity.vmFolder
            elif isinstance(entity, vim.VirtualMachine):
                # Don't descend further, since we don't expect a VM to have
                # any child entities that are VMs.
                continue

            vm = content.searchIndex.FindChild(entity, name)
            if vm is not None:
                return vm
            entities.extend(
                e for e in entity.childEntity
                if not isinstance(e, vim.VirtualMachine))
        return None

    def _get_obj(self, vimtype, name, root=None):
        # Get the vsphere object associated with a given text name
        content = self._get_content()
        if not root:
            root = content.rootFolder

        container = content.viewManager.CreateContainerView(root, vimtype,
                                                            True)
        for c in container.view:
            try:
                if c.name == name:
                    return c
            except vmodl.fault.ManagedObjectNotFound:
                # Managed object has been removed, is being created, etc. Skip.
                pass
        return None

    def _get_vm_by_name_via_properties(self, name, root=None):
        content = self._get_content()
        if not root:
            root = content.rootFolder
        container = content.viewManager.CreateContainerView(
                root, [vim.VirtualMachine], True)

        collector = content.propertyCollector

        # Create object specification to define the starting point of
        # inventory navigation
        obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = container
        obj_spec.skip = True

        # Create a traversal specification to identify the path for collection
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = container.__class__
        obj_spec.selectSet = [traversal_spec]

        # Identify the properties to the retrieved
        property_spec = vmodl.query.PropertyCollector.PropertySpec()
        property_spec.type = vim.VirtualMachine

        property_spec.all = True
        property_spec.pathSet = None

        # Add the object and property specification to the
        # property filter specification
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]

        # Retrieve properties
        props = collector.RetrieveContents([filter_spec])

        # data = []
        # for obj in props:
        #    properties = {}
        #    for prop in obj.propSet:
        #        properties[prop.name] = prop.val
        #
        #    properties['obj'] = obj.obj
        #
        #    data.append(properties)
        # return data
        for obj in props:
            return obj.obj

    def _get_all_objs(self, vimtype, root=None):
        # Get all vsphere objects associated with a given type
        content = self._get_content()
        if not root:
            root = content.rootFolder
        container = content.viewManager.CreateContainerView(root, vimtype,
                                                            True)
        return {x: x.name for x in container.view}

    def _get_by_properties(self, view_ref, obj_type, path_set=None,
                           include_mors=False):
        """
        Collect properties for managed objects from a view ref
        Check the vSphere API documentation for example on retrieving
        object properties:
            - http://goo.gl/erbFDz
        Args:
            si          (ServiceInstance): ServiceInstance connection
            view_ref (pyVmomi.vim.view.*): Starting point of inventory nav
            obj_type      (pyVmomi.vim.*): Type of managed object
            path_set               (list): List of properties to retrieve
            include_mors           (bool): If True include the managed objects
                                           refs in the result
        Returns:
            A list of properties for the managed objects

        Code adapted from:
        https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/tools/pchelper.py
        """
        service_instance = self._get_si()
        collector = service_instance.content.propertyCollector

        # Create object specification to define the starting point of
        # inventory navigation
        obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True

        # Create a traversal specification to identify the path for collection
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__
        obj_spec.selectSet = [traversal_spec]

        # Identify the properties to the retrieved
        property_spec = vmodl.query.PropertyCollector.PropertySpec()
        property_spec.type = obj_type

        if not path_set:
            property_spec.all = True

        property_spec.pathSet = path_set

        # Add the object and property specification to the
        # property filter specification
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]

        # Retrieve properties
        props = collector.RetrieveContents([filter_spec])

        data = []
        for obj in props:
            properties = {}
            for prop in obj.propSet:
                properties[prop.name] = prop.val

            if include_mors:
                properties['obj'] = obj.obj

            data.append(properties)
        return data

    def _get_container_view(self, obj_type, container=None):
        """
        Get a vSphere Container View ref to all objects of type 'obj_type'
        It is up to the caller to take care of destroying the View when no
        longer needed.
        Args:
            obj_type (list): A list of managed object types
        Returns:
            A container view ref to the discovered managed objects

        Code adapted from:
        https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/tools/pchelper.py
        """
        service_instance = self._get_si()

        if not container:
            container = service_instance.content.rootFolder

        view_ref = service_instance.content.viewManager.CreateContainerView(
            container=container,
            type=obj_type,
            recursive=True
        )
        return view_ref

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

    def login(self, server=None, username=None, password=None, prompt=None):
        """
        Conduct a console login

        * prompt: Controls if a TTY prompt for credentials should be made
        """
        if prompt is None and not (username and password):
            warnings.warn(DeprecationWarning("Prompt's default value will change from True to False in the future"))
            prompt = True

        if prompt:
            if not username:
                sys.stderr.write(" Username: ")
                username = input()
            if not password:
                password = getpass.getpass(prompt=" Password: ")

        self.si = self._resources.enter_context(
            SmartConnection(host=server, user=username, pwd=password,
                         port=443)
        )
        # pyVim should either return this or raise an exception
        assert self.si

        # Useful for chained forms? Odd for .login()
        return self

    # General methods

    def get_cluster_by_name(self, name, root=None):
        """
        Find a cluster by it's name and return it
        """
        # CORRY: Why is the caller required to wrap in a list[] if everyone
        #        passes a single item?
        return self._get_obj([vim.ClusterComputeResource], name, root)

    def get_clusters(self, root=None):
        """
        Returns all clusters
        """
        return self._get_all_objs([vim.ClusterComputeResource], root)

    def get_datastore_clusters(self, root=None):
        """
        Returns all Datastore clusters
        """
        return self._get_all_objs([vim.StoragePod], root)

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

    def get_simple_network_by_name(self, name, root=None):
        """
        Find a simple-switch virtual network by it's name and return it
        """
        return self._get_obj([vim.Network], name, root)

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

    def get_tiers_in_datacenter(self, datacenter, root=None):
        """
        Returns hosts in Datacenter
        """
        hosts = []
        for cluster in self.get_datacenter_by_name(datacenter).hostFolder.childEntity:
            hosts.append(cluster)

        return sorted(hosts, key=lambda host: host.name)

    def get_vm_by_name_old(self, name, root=None):
        return self._get_obj([vim.VirtualMachine], name, root)

    def get_vm_by_name(self, name, root=None):
        """
        Find a virtual machine by it's name and return it
        """
        if root is None:
            content = self._get_content()
            vm = content.searchIndex.FindByDnsName(dnsName=name, vmSearch=True)
            if vm is not None and vm.name == name:
                return vm
            # Fall back to recursive index searches over all groups/folders of
            # VMs within the global space.  This will discover those VMs that
            # don't match their DNS name.
            return self._find_vm_by_name(name)
        return self._get_obj([vim.VirtualMachine], name, root)
        # return self._get_vm_by_name_via_properties(name, root)

    def get_vms_in_clusters(self, name, root=None):
        """
        return all vms inside cluster. Must supply a list.
        """
        all_vms = []
        for clustergroups in name:
            tier = self.get_cluster_by_name(clustergroups)
            for host in tier.host:
                vms = host.vm
                vms_list = []
                for vmname in vms:
                    vms_list.append(vmname)
                for individual_vms in vms_list:
                    all_vms.append(individual_vms)
        return all_vms

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
            if system_ready and system_state == 'running' and \
                    system_uptime > 90:
                break
            time.sleep(10)
            # CORRY: Consider a maximum wait time, throw exception

    def login_in_guest(username, password):
        return vim.vm.guest.NamePasswordAuthentication(username=username,
                                                       password=password)

    def start_process(si, vm, auth, program_path, args=None, env=None,
                      cwd=None):
        cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(
                arguments=args, programPath=program_path, envVariables=env,
                workingDirectory=cwd)
        cmdpid = si.content.guestOperationsManager.processManager.StartProgramInGuest(
                vm=vm, auth=auth, spec=cmdspec)
        return cmdpid

    def vmotion_vm(self, vm_name, host_name=None, datastore_name=None,
                   cluster_name=None):
        cluster_ref = None
        datastore_ref = None
        host_ref = None
        pool_ref = None
        vm_ref = None

        # Right now, to migrate across clusters you MUST pass a cluster param

        vm_ref = self.get_vm_by_name(vm_name)
        assert vm_ref is not None

        if host_name is not None:
            host_ref = self.get_host_by_name(host_name)
            assert host_ref is not None

            for candidate in host_ref.datastore:
                if candidate.name == datastore_name:
                    datastore_ref = candidate
                    break

        if cluster_name is not None:
            cluster_ref = self.get_cluster_by_name(cluster_name)
            assert cluster_ref is not None

            pool_ref = cluster_ref.resourcePool

            for candidate in cluster_ref.datastore:
                if candidate.name == datastore_name:
                    datastore_ref = candidate
                    break

        if datastore_ref is None:
            print(("Can't find volume {}".format(datastore_name)))
            sys.exit(1)

        relocate_spec = vim.vm.RelocateSpec()
        relocate_spec.datastore = datastore_ref
        relocate_spec.host = host_ref
        relocate_spec.pool = pool_ref

        pprint.pprint(relocate_spec)

        return vm_ref.Relocate(relocate_spec)

    def wait_for_tasks(self, tasks):
        """
        Given a list of tasks, this method blocks until all tasks are complete
        """
        si = self._get_si()
        pc = si.content.propertyCollector

        taskList = [str(task) for task in tasks]

        # Create filter
        objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                    for task in tasks]
        propSpec = vmodl.query.PropertyCollector.PropertySpec(
                type=vim.Task, pathSet=[], all=True)
        filterSpec = vmodl.query.PropertyCollector.FilterSpec()
        filterSpec.objectSet = objSpecs
        filterSpec.propSet = [propSpec]

        filterRef = pc.CreateFilter(filterSpec, True)

        try:
            version, state = None, None

            # Loop looking for updates till the state moves to completed state.
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
