from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import atexit, getpass, sys, time

class vmQuick:
  def __init__(self,server=None,username=None,password=None):
    self.content = None
    self.si = None
    if server:
      self.login(server,username,password)

  ### Private Methods

  def _get_obj(self, vimtype, name, root=None):
      # Get the vsphere object associated with a given text name
      content = self._get_content()
      if not root:
        root=content.rootFolder
      obj = None
      container = content.viewManager.CreateContainerView(root, vimtype, True)
      for c in container.view:
          if c.name == name:
              obj = c
              break
      return obj

  def _get_all_objs(self, vimtype, root=None):
      # Get all vsphere objects associated with a given type
      content = self._get_content()
      if not root:
        root=content.rootFolder
      obj = {}
      container = content.viewManager.CreateContainerView(root, vimtype, True)
      for c in container.view:
          obj.update({c: c.name})
      return obj

  ### Cache common references

  def _get_si(self):
    if not self.si:
      login()
    return self.si

  def _get_content(self):
    if not self.content:
      si = self._get_si()
      self.content = si.RetrieveContent()
    return self.content

  ### Login method

  def login(self,server=None,username=None,password=None):
      """
      Conduct a console login
      """
      self.si = None

      if not username:
        sys.stderr.write(" Username: ")
        username = raw_input()
      if not password:
        password = getpass.getpass(prompt=" Password: ")    

      try:
        self.si = SmartConnect(host=server, user=username, pwd=password, port=443)
      except IOError, e:
        pass
     
      if not self.si:
        print "Could not connect to vCenter using specified username and password"
        sys.exit(1)

      atexit.register(Disconnect, self.si)
      return self

  ### General methods

  def get_cluster_by_name(self, name):
      """
      Find a cluster by it's name and return it
      """
      return self._get_obj([vim.ClusterComputeResource], name)

  def get_clusters(self):
      """
      Returns all clusters
      """
      return self._get_all_objs([vim.ClusterComputeResource])

  def get_datacenter_by_name(self, name):
      """
      Find a datacenter by it's name and return it
      """
      return self._get_obj([vim.Datacenter], name)

  def get_datacenters(self):
      """
      Returns all datacenters
      """
      return self._get_all_objs([vim.Datacenter])

  def get_datastore_by_name(self, name):
      """
      Find a datastore by it's name and return it
      """
      return self._get_obj([vim.Datastore], name)

  def get_datastores(self):
      """
      Returns all datastores
      """
      return self._get_all_objs([vim.Datastore])

  def get_folder_by_name(self, name, root=None):
      """
      Find a folder by it's name and return it
      """
      return self._get_obj([vim.Folder], name, root)

  def get_folders(self,root=None):
      """
      Returns all datastores
      """
      return self._get_all_objs([vim.Folder], root)

  def get_host_by_name(self, name, root=None):
      """
      Find a virtual machine by it's name and return it
      """
      return self._get_obj([vim.HostSystem], name, root)

  def get_hosts(self,root=None):
      """
      Returns all hosts
      """
      raw_hosts = self._get_all_objs([vim.HostSystem], root)
      hosts = []
      for host in sorted(raw_hosts,key=lambda host: host.name):
        hosts.append(host)
      return hosts

  def get_registered_vms(self):
      """
      Returns all vms
      """
      raw_vms = self._get_all_objs([vim.VirtualMachine])
      vms = []
      for vm in sorted(raw_vms,key=lambda vm: vm.summary.config.name):    
        vms.append(vm)
      return vms

  def get_resource_pool(self, name):
      """
      Find a virtual machine by it's name and return it
      """
      return self._get_obj([vim.ResourcePool], name)

  def get_resource_pools(self):
      """
      Returns all resource pools
      """
      return self._get_all_objs([vim.ResourcePool])

  def get_vm_by_name(self, name):
      """
      Find a virtual machine by it's name and return it
      """
      return self._get_obj([vim.VirtualMachine], name)

  def is_ready(vm):
      while True:
          system_ready = vm.guest.guestOperationsReady
          system_state = vm.guest.guestState
          system_uptime = vm.summary.quickStats.uptimeSeconds
          if system_ready and system_state == 'running' and system_uptime > 90:
              break
          time.sleep(10)

  def login_in_guest(username, password):
      return vim.vm.guest.NamePasswordAuthentication(username=username,password=password)

  def start_process(si, vm, auth, program_path, args=None, env=None, cwd=None):
      cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args, programPath=program_path, envVariables=env, workingDirectory=cwd)
      cmdpid = si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=auth, spec=cmdspec)
      return cmdpid

  def storage_vmotion_vm(si,vm_name,storage_name):
     vm = get_vm_by_name(si, vm_name)
     host = vm.summary.runtime.host

     ds = None
     for candidate in host.datastore:
        if candidate.name == storage_name:
           ds = candidate
           break

     if ds is None:
        print "Can't find volume {} on host {}".fomat(storage_name,host.name)
        sys.exit(1)

     #print "Moving '{}' to '{}' on '{}'".format(vm.name,ds.name,host.name)

     relocate_spec = vim.vm.RelocateSpec()
     relocate_spec.datastore = ds

     return vm.Relocate(relocate_spec)

  def vmotion_vm(si,vm_name,host_name,storage_name):
     vm = get_vm_by_name(si, vm_name)
     host = get_host_by_name(si, host_name)

     ds = None
     for candidate in host.datastore:
        if candidate.name == storage_name:
           ds = candidate
           break

     if ds is None:
        print "Can't find volume {} on host {}".fomat(storage_name,host.name)
        sys.exit(1)

     relocate_spec = vim.vm.RelocateSpec(host=host)
     relocate_spec.datastore = ds
     #relocate_spec.host = host

     print relocate_spec

     return vm.Relocate(relocate_spec)

  def wait_for_tasks(self, tasks):
     """
     Given the service instance si and tasks, it returns after all the
     tasks are complete
     """
     si = self._get_si()
     pc = si.content.propertyCollector

     taskList = [str(task) for task in tasks]

     # Create filter
     objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                                                              for task in tasks]
     propSpec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                           pathSet=[], all=True)
     filterSpec = vmodl.query.PropertyCollector.FilterSpec()
     filterSpec.objectSet = objSpecs
     filterSpec.propSet = [propSpec]
     filter = pc.CreateFilter(filterSpec, True)

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
        if filter:
           filter.Destroy()
