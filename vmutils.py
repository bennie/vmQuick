from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import atexit
import getpass
import sys
import time

def _get_obj(content, vimtype, name, root=None):
    """
    Get the vsphere object associated with a given text name
    """
    if not root:
      root=content.rootFolder
    obj = None
    container = content.viewManager.CreateContainerView(root, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def _get_all_objs(content, vimtype, root=None):
    """
    Get all the vsphere objects associated with a given type
    """
    if not root:
      root=content.rootFolder
    obj = {}
    container = content.viewManager.CreateContainerView(root, vimtype, True)
    for c in container.view:
        obj.update({c: c.name})
    return obj

def login_in_guest(username, password):
    return vim.vm.guest.NamePasswordAuthentication(username=username,password=password)

def start_process(si, vm, auth, program_path, args=None, env=None, cwd=None):
    cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args, programPath=program_path, envVariables=env, workingDirectory=cwd)
    cmdpid = si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=auth, spec=cmdspec)
    return cmdpid

def get_cluster_by_name(si, name):
    """
    Find a cluster by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.ClusterComputeResource], name)

def get_clusters(si):
    """
    Returns all clusters
    """
    return _get_all_objs(si.RetrieveContent(), [vim.ClusterComputeResource])

def get_datacenter_by_name(si, name):
    """
    Find a datacenter by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.Datacenter], name)

def get_datacenters(si):
    """
    Returns all datacenters
    """
    return _get_all_objs(si.RetrieveContent(), [vim.Datacenter])

def get_datastore_by_name(si, name):
    """
    Find a datastore by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.Datastore], name)

def get_datastores(si):
    """
    Returns all datastores
    """
    return _get_all_objs(si.RetrieveContent(), [vim.Datastore])

def get_folder_by_name(si, name, root=None):
    """
    Find a folder by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.Folder], name, root)

def get_folders(si,root=None):
    """
    Returns all datastores
    """
    return _get_all_objs(si.RetrieveContent(), [vim.Folder], root)

def get_host_by_name(si, name, root=None):
    """
    Find a virtual machine by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.HostSystem], name, root)

def get_hosts(si,root=None):
    """
    Returns all hosts
    """
    raw_hosts = _get_all_objs(si.RetrieveContent(), [vim.HostSystem], root)
    hosts = []
    for host in sorted(raw_hosts,key=lambda host: host.name):
      hosts.append(host)
    return hosts

def get_registered_vms(si):
    """
    Returns all vms
    """
    raw_vms = _get_all_objs(si.RetrieveContent(), [vim.VirtualMachine])
    vms = []
    for vm in sorted(raw_vms,key=lambda vm: vm.summary.config.name):    
      vms.append(vm)
    return vms

def get_resource_pool(si, name):
    """
    Find a virtual machine by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.ResourcePool], name)

def get_resource_pools(si):
    """
    Returns all resource pools
    """
    return _get_all_objs(si.RetrieveContent(), [vim.ResourcePool])

def get_vm_by_name(si, name):
    """
    Find a virtual machine by it's name and return it
    """
    return _get_obj(si.RetrieveContent(), [vim.VirtualMachine], name)

def is_ready(vm):
    while True:
        system_ready = vm.guest.guestOperationsReady
        system_state = vm.guest.guestState
        system_uptime = vm.summary.quickStats.uptimeSeconds
        if system_ready and system_state == 'running' and system_uptime > 90:
            break
        time.sleep(10)

def login(server,username=None,password=None):
    """
    Conduct a console login
    """
    si = None

    if not username:
      sys.stderr.write(" Username: ")
      username = raw_input()
    if not password:
      password = getpass.getpass(prompt=" Password: ")    

    try:
      si = SmartConnect(host=server, user=username, pwd=password, port=443)
    except IOError, e:
      pass
   
    if not si:
      print "Could not connect to vCenter using specified username and password"
      sys.exit(1)

    atexit.register(Disconnect, si)
    return si

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

def wait_for_tasks(si, tasks):
   """
   Given the service instance si and tasks, it returns after all the
   tasks are complete
   """

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
