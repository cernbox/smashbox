from smashbox.script import config

import os.path
import datetime
import subprocess
import time

# Utilities to be used in the test-cases.

######## TEST SETUP AND PREPARATION

def reset_owncloud_account(reset_procedure=None,numTestUsers=None):
    """ 
    Prepare the test account on the owncloud server (remote state). Run this once at the beginning of the test.

    The reset_procedure defines what actually happens. If not set then the config default oc_account_reset_procedure applies.
    
    Normally the account is deleted and recreated ('delete')

    If reset_procedure is set to 'keep' than the account is not deleted, so the state from the previous run is kept.

    """
    if reset_procedure is None:
        reset_procedure = config.oc_account_reset_procedure

    if numTestUsers is None:
        numTestUsers = config.oc_number_test_users

    logger.info('reset_owncloud_account (%s) for %i users', reset_procedure, numTestUsers)

    if reset_procedure == 'delete':
        for i in range(1, numTestUsers+1):
            username = "%s%i"%(config.oc_account_name, i)
            delete_owncloud_account(username)
            create_owncloud_account(username,config.oc_account_password)

        return

    if reset_procedure == 'webdav_delete':
        webdav_delete('/') # delete the complete webdav endpoint associated with the remote account
        webdav_delete('/') # FIXME: workaround current bug in EOS (https://savannah.cern.ch/bugs/index.php?104661) 

    # if create if does not exist (for keep or webdav_delete options)
    webdav_mkcol('/') 

def reset_rundir(reset_procedure=None):
    """ Prepare the run directory for the current test (local state). Run this once at the beginning of the test.

    The reset_procedure defines what actually happens. If not set then the config default rundir_reset_procedure applies.

    Normally the run directory is deleted ('delete'). To keep the local run directory intact specify "keep".

    """
    if reset_procedure is None:
        reset_procedure = config.rundir_reset_procedure

    logger.info('reset_rundir (%s)', reset_procedure)

    #assert(config.rundir)
    # that's a bit dangerous... so let's try to mitiage the risk
    
    if reset_procedure == 'delete':
        assert( os.path.realpath(config.rundir).startswith(os.path.realpath(config.smashdir)) )
        removeTree(config.rundir)

def make_workdir(name=None):
    """ Create a worker directory in the current run directory for the test (by default the name is derived from the worker's name). 
    """
    from smashbox.utilities import reflection
    if name is None:
        name = reflection.getProcessName()

    d = os.path.join(config.rundir,name)
    mkdir(d)
    logger.info('make_workdir %s',d)
    return d

def create_owncloud_account(user=None,password=None):
    if user is None:
        user = config.oc_account_name
    if password is None:
        password = config.oc_account_password

    logger.info('create_owncloud_account: %s',user)    
    runcmd('%s sudo -u %s php %s/create_user.php %s %s'%(config.oc_server_shell_cmd,config.web_user,config.oc_server_tools_path,user,password))

def delete_owncloud_account(user):
    logger.info('delete_owncloud_account: %s',user)    
    runcmd('%s sudo -u %s php %s/delete_user.php %s'%(config.oc_server_shell_cmd,config.web_user,config.oc_server_tools_path,user))

def check_owncloud_account(user):
    logger.info('check_owncloud_account: %s',user)    
    runcmd('%s sudo -u %s php %s/check_user.php %s'%(config.oc_server_shell_cmd,config.web_user,config.oc_server_tools_path,user))

def reset_owncloud_group(numGroups=None):
    logger.info('reset_owncloud_group for group: %s', config.oc_group_name)

    if numGroups is None:
        numGroups = config.oc_number_test_groups

    for i in range(1, numGroups+1):
        groupname = "%s%i"%(config.oc_group_name, i)
        delete_owncloud_group(groupname)
        create_owncloud_group(groupname)

def  check_owncloud_group(group):
    logger.info('check_owncloud_group for group: %s', group)
    runcmd('%s sudo -u %s php %s/check_group.php %s'%(config.oc_server_shell_cmd,config.web_user,config.oc_server_tools_path,group))

def  delete_owncloud_group(group):
    logger.info('delete_owncloud_group for group: %s', group)
    runcmd('%s sudo -u %s php %s/delete_group.php %s'%(config.oc_server_shell_cmd,config.web_user,config.oc_server_tools_path,group))

def  create_owncloud_group(group):
    logger.info('create_owncloud_group for group: %s', group)
    runcmd('%s sudo -u %s php %s/create_group.php %s'%(config.oc_server_shell_cmd,config.web_user,config.oc_server_tools_path,group))

######### WEBDAV AND SYNC UTILITIES #####################

def oc_webdav_url(protocol='http',remote_folder="",userNum=1):
  """ Protocol for sync client should be set to 'owncloud'. Protocol for generic webdav clients is http.
  """
      
  if config.oc_ssl_enabled:
      protocol += 's'

      
  remote_folder = remote_folder.lstrip('/') # strip-off any leading / characters to prevent 1) abspath result from the join below, 2) double // and alike...

  remote_path = os.path.join(config.oc_webdav_endpoint,config.oc_server_folder,remote_folder)

  #remote_path = os.path.join('owncloud/remote.php/webdav',remote_folder)  # this is for standard owncloud 

#   return protocol+('://%(oc_account_name)s:%(oc_account_password)s@%(oc_server)s/'%config)+remote_path

  username = "%s%i"%(config.oc_account_name, userNum)
  return protocol + '://' + username + (':%(oc_account_password)s@%(oc_server)s/'%config)+remote_path


# this is a local variable for each worker that keeps track of the repeat count for the current step
ocsync_cnt = {}

def run_ocsync(local_folder,remote_folder="",N=None,userNum=1):
    """ Run the ocsync for local_folder against remote_folder (or the main folder on the owncloud account if remote_folder is None).
    Repeat the sync N times. If N not given then N -> config.oc_sync_repeat (default 1).
    """
    global ocsync_cnt
    from smashbox.utilities import reflection
    if N is None:
        N = config.oc_sync_repeat

    current_step = reflection.getCurrentStep()

    ocsync_cnt.setdefault(current_step,0)

    local_folder += '/' #FIXME: HACK - is a trailing slash really needed by 1.6 owncloudcmd client?

    for i in range(N):
        t0 = datetime.datetime.now()
#        cmd = config.oc_sync_cmd+' '+local_folder+' '+oc_webdav_url('owncloud',remote_folder,userNum)+" >> "+ config.rundir+"/%s-ocsync.step%02d.cnt%03d.log 2>&1"%(reflection.getProcessName(),current_step,ocsync_cnt[current_step])
        cmd = config.oc_sync_cmd+' '+local_folder+' '+oc_webdav_url(config.oc_root,remote_folder,userNum)+" >> "+ config.rundir+"/%s-ocsync.step%02d.cnt%03d.log 2>&1"%(reflection.getProcessName(),current_step,ocsync_cnt[current_step])
        runcmd(cmd,ignore_exitcode=True) # exitcode of ocsync is not reliable
        logger.info('sync cmd is: %s',cmd)
        logger.info('sync finished: %s',datetime.datetime.now()-t0)
        ocsync_cnt[current_step]+=1

def webdav_propfind_ls(path):
    runcmd('curl -s -k -XPROPFIND %s | xmllint --format -'%oc_webdav_url(remote_folder=path))

def webdav_delete(path):
    runcmd('curl -k -X DELETE %s '%oc_webdav_url(remote_folder=path))

def webdav_mkcol(path,silent=False):
    out=""
    if silent: # a workaround for super-verbose errors in case directory on the server already exists
        out = "> /dev/null 2>&1"
    runcmd('curl -k -X MKCOL %s %s'%(oc_webdav_url(remote_folder=path),out))
                   

##### SHELL COMMANDS AND TIME FUNCTIONS
        
def runcmd(cmd,ignore_exitcode=False,echo=True,allow_stderr=True,shell=True):
    logger.info('running %s',repr(cmd))

    process=subprocess.Popen(cmd,shell=shell,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if echo:
        if stdout.strip():
            logger.info("stdout: %s",stdout)
        if stderr.strip():
            if allow_stderr:
                logger.info("stderr: %s",stderr)
            else:
                logger.error("stderr: %s",stderr)

    if process.returncode != 0:
        msg = "Non-zero exit code %d from command %s" % (process.returncode,repr(cmd))
        if ignore_exitcode:
            logger.warning(msg)
            return process.returncode
        else:
            raise subprocess.CalledProcessError(process.returncode,cmd)

    return process.returncode

def sleep(n):
    logger.info('sleeping %s seconds',n)
    time.sleep(n)

        
######## BASIC FILE AND DIRECTORY OPERATIONS
        
def mkdir(d):
    runcmd('mkdir -p '+d)
    return d

def removeTree(path):
    runcmd('rm -rf '+path)

def removeFile(path):
    logger.info('remove file %s',path)
    try:
        os.remove(path)
    except OSError,x:
        import errno
        if x.errno == errno.ENOENT:
            logger.warning(x)
        else:
            raise

def mv(a,b):
    runcmd('mv %s %s'%(a,b))


def list_files(path,recursive=False):
    if recursive:
        runcmd('ls -lR %s'%path)
    else:
        runcmd('ls -l %s'%path)



### DATA FILES AND VERSIONS

def createfile(fn,c,count,bs):
    # this replaces the dd as 1) more portable, 2) not prone to problems with escaping funny filenames in shell commands
    logger.info('createfile %s character=%s count=%d bs=%d',fn,repr(c),count,bs)
    buf = c*bs
    of = file(fn,'w')
    for i in range(count):
        of.write(buf)
    of.close()

def modifyFile(fn,c,count,bs):

    logger.info('modifyFile %s character=%s count=%d bs=%d',fn,repr(c),count,bs)
    buf = c*bs

    if not os.path.exists(fn):
        message = fn + ' does not exist'
        logger.error(message)
        reported_errors.append(message)
        return

    if not os.path.isfile(fn):
        message = fn + ' is not a file'
        logger.error(message)
        reported_errors.append(message)
        return

    of = open(fn,'a')
    pos = of.seek (0,2)
    for i in range(count):
        logger.info ('modifyFile: appending ')
        of.write(buf)
    of.close()

def deleteFile(fn):

    logger.info('deleteFile: deleting file %s ',fn)
    if os.path.exists(fn):
        os.remove(fn)

def createfile_zero(fn,count,bs):
    createfile(fn,'\0',count,bs)

import platform

if platform.system() == 'Darwin':

 def md5sum(fn):
    process=subprocess.Popen('md5 %s'%fn,shell=True,stdout=subprocess.PIPE)
    out = process.communicate()[0]
    try:
        return out.split()[-1]
    except IndexError:
        return "NO_CHECKSUM_ERROR"

else: #linux

 def md5sum(fn):
    process=subprocess.Popen('md5sum %s'%fn,shell=True,stdout=subprocess.PIPE)
    out = process.communicate()[0]
    return out.split()[0]

def hexdump(fn):
    runcmd('hexdump %s'%fn)

def list_versions_on_server(fn):
    cmd = "%(oc_server_shell_cmd)s md5sum %(oc_server_datadirectory)s/%(oc_account_name)s/files_versions/%(filename)s.v*" % config._dict(filename=os.path.join(config.oc_server_folder,os.path.basename(fn))) #PENDING: bash -x 
    runcmd(cmd)


def hexdump_versions_on_server(fn):
    cmd = "%(oc_server_shell_cmd)s hexdump %(oc_server_datadirectory)s/%(oc_account_name)s/files_versions/%(filename)s.v*" % config._dict(filename=os.path.join(config.oc_server_folder,os.path.basename(fn))) #PENDING: bash -x 
    runcmd(cmd)    

def get_md5_versions_on_server(fn):

    cmd = "%(oc_server_shell_cmd)s md5sum %(oc_server_datadirectory)s/%(oc_account_name)s/files_versions/%(filename)s.v*" % config._dict(filename=os.path.join(config.oc_server_folder,os.path.basename(fn)))

    logger.info('running %s',repr(cmd))
    process=subprocess.Popen(cmd, stdout=subprocess.PIPE,shell=True)

    stdout=process.communicate()[0]

    result = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        md,fn = line.split()
        result.append((md,os.path.basename(fn)))
        #log(result[-1])

    return result

####### LOGIC OPERANDS  ############

def implies(p,q):
    return not p or q;

####### ERROR REPORTING ############

reported_errors = []

def error_check(expr,message):
    """ Assert expr is True. If not, then mark the test as failed but carry on the execution.
    """
    if not expr:
        logger.error(message)
        reported_errors.append(message)

def fatal_check(expr,message):
    """ Assert expr is True. If not, then mark the test as failed and stop immediately.
    """    
    if not expr:
        logger.fatal(message)
        reported_errors.append(message)
        raise AssertionError(message)


####### Provisioning API Calls ############

def get_oc_api ():

    from smashbox.utilities import ownCloudWebDav

    protocol = 'http'
    if config.oc_ssl_enabled:
      protocol += 's'

    url = protocol + '://' + config.oc_server + '/' + config.oc_root
    ocApi = ownCloudWebDav.ownCloudWebDav(url)
    return ocApi

def shareFileWithUser (filename, sharer, sharee, **kwargs):

    logger.info('%s is sharing file %s with user %s', sharer, filename, sharee) 

    ocApi = get_oc_api()
    ocApi.login (sharer, config.oc_account_password)
    shareInfo = ocApi.share_file_with_user (filename, sharee, **kwargs)

    logger.info('share id for file share is %s', str(shareInfo.share_id)) 
    return shareInfo.share_id

def deleteShare (sharer, share_id):

    logger.info('Deleting share %i from user %s', share_id, sharer) 

    ocApi = get_oc_api()
    ocApi.login (sharer, config.oc_account_password)
    ocApi.delete_share (share_id)

def shareFileWithGroup (filename, sharer, group, **kwargs):

    logger.info('%s is sharing file %s with group %s', sharer, filename, group) 

    ocApi = get_oc_api()
    ocApi.login (sharer, config.oc_account_password)
    groupShareInfo = ocApi.share_file_with_group (filename, group, **kwargs)

    logger.info('share id for file group share is %i', groupShareInfo.share_id)
    return groupShareInfo.share_id

def addUserToGroup (username, groupName):

    logger.info('Adding user %s to group %s', username, groupName) 

    ocApi = get_oc_api()
    ocApi.login (config.oc_admin_user, config.oc_admin_password)
    ocApi.add_user_to_group (username, groupName)

def removeUserFromGroup (username, groupName):

    logger.info('Removing user %s from group %s', username, groupName) 

    ocApi = get_oc_api()
    ocApi.login (config.oc_admin_user, config.oc_admin_password)
    ocApi.remove_user_from_group (username, groupName)

def getShareId (path, filename, **kwargs):

    logger.info('Getting the share id for file %s from directory %s', filename, path) 

    ocApi = get_oc_api()
    ocApi.login (config.oc_admin_user, config.oc_admin_password)
#    fullPath = "%s/%s"%(config.rundir, path)
    shares = ocApi.get_shares (path, **kwargs)

    for i in range(1, len(shares)):
        logger.info ('jrmhere: share is %s', shares[i])

