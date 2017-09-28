from smashbox.script import config

import os.path
import datetime
import subprocess
import time
import urllib
import platform
import shutil

# Utilities to be used in the test-cases.

def OWNCLOUD_CHUNK_SIZE(factor=1):
    """Calculate file size as a fraction of owncloud client's default chunk size.
    """
    return int(20*1024*1024*factor) # 20MB as of client 1.7 


######## TEST SETUP AND PREPARATION

def setup_test():
    """ Setup hooks run before any worker kicks-in. 
    This is run under the name of the "supervisor" worker.

    The behaviour of these hooks is entirely controlled by config
    options. It should be possible to disable optional hooks by
    configuration.

    If exception is raised then the testcase execution is aborted and smashbox terminates with non-zero exit code,

    """
    reset_owncloud_account(num_test_users=config.oc_number_test_users)
    reset_rundir()
    reset_server_log_file()
    

def finalize_test():
    """ Finalize hooks run after last worker terminated.
    This is run under the name of the "supervisor" worker.

    The behaviour of these hooks is entirely controlled by config
    options. It should be possible to disable optional hooks by
    configuration.
    
    If exception is raised then smashbox terminates with non-zero exit code,
    """
    d = make_workdir()
    scrape_log_file(d)

######### HELPERS

def reset_owncloud_account(reset_procedure=None, num_test_users=None):
    """ 
    Prepare the test account on the owncloud server (remote state). Run this once at the beginning of the test.

    The reset_procedure defines what actually happens. If not set then the config default oc_account_reset_procedure
    applies.
    
    Normally the account is deleted and recreated ('delete')

    If reset_procedure is set to 'keep' than the account is not deleted, so the state from the previous run is kept.

    """
    if reset_procedure is None:
        reset_procedure = config.oc_account_reset_procedure

    if num_test_users is None:
        logger.info('reset_owncloud_account (%s)', reset_procedure)

    else:
        logger.info('reset_owncloud_account (%s) for %d users', reset_procedure, num_test_users)

    if reset_procedure == 'delete':
        delete_owncloud_account(config.oc_account_name)
        create_owncloud_account(config.oc_account_name, config.oc_account_password)
        login_owncloud_account(config.oc_account_name, config.oc_account_password)

        if num_test_users is not None:
            for i in range(1, num_test_users + 1):
                username = "%s%i" % (config.oc_account_name, i)
                delete_owncloud_account(username)
                create_owncloud_account(username, config.oc_account_password)
                login_owncloud_account(username, config.oc_account_password)

        return

    if reset_procedure == 'webdav_delete':
        webdav_delete('/') # delete the complete webdav endpoint associated with the remote account
        webdav_delete('/') # FIXME: workaround current bug in EOS (https://savannah.cern.ch/bugs/index.php?104661) 

    # if create if does not exist (for keep or webdav_delete options)
    webdav_mkcol('/')


def reset_rundir(reset_procedure=None):
    """ Prepare the run directory for the current test (local state). Run this once at the beginning of the test.

    The reset_procedure defines what actually happens. If not set then the config default rundir_reset_procedure 
    applies.

    Normally the run directory is deleted ('delete'). To keep the local run directory intact specify "keep".

    """
    if reset_procedure is None:
        reset_procedure = config.rundir_reset_procedure

    logger.info('reset_rundir (%s)', reset_procedure)

    # assert(config.rundir)
    # that's a bit dangerous... so let's try to mitiage the risk

    if reset_procedure == 'delete':
        assert(os.path.realpath(config.rundir).startswith(os.path.realpath(config.smashdir)))
        remove_tree(config.rundir)
        mkdir(config.rundir)


def make_workdir(name=None):
    """ Create a worker directory in the current run directory for the test (by default the name is derived from 
    the worker's name). 
    """
    from smashbox.utilities import reflection

    if name is None:
        name = reflection.getProcessName()

    d = os.path.join(config.rundir,name)
    mkdir(d)
    logger.info('make_workdir %s',d)
    return d


def create_owncloud_account(username=None, password=None):
    """ Creates a user account on the server

    :param username: name of the user to be created, if None then the username is retrieved from the config file
    :param password: password for the user, if None then the password is retrieved from the config file

    """
    if username is None:
        username = config.oc_account_name
    if password is None:
        password = config.oc_account_password

    logger.info('Creating user %s with password %s', username, password)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    oc_api.create_user(username, password)


def login_owncloud_account(username=None, password=None):
    """ Login as user on the server (to generate the encryption keys)

    :param username: name of the user to be logged in
    :param password: password for the user

    """
    if username is None:
        username = config.oc_account_name
    if password is None:
        password = config.oc_account_password

    logger.info('Logging in user %s with password %s', username, password)

    oc_api = get_oc_api()
    oc_api.login(username, password)

def delete_owncloud_account(username):
    """ Deletes a user account on the server

    :param username: name of the user to be created

    """
    logger.info('Deleting user %s', username)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    oc_api.delete_user(username)


def check_owncloud_account(username):
    """ Checks if a user account exists on the server

    :param user: name of the user to be checked

    """
    logger.info('Checking if user %s exists', username)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    exists = oc_api.user_exists(username)
    return exists


def reset_owncloud_group(num_groups=None):
    """ Deletes and recreates groups on the server

    :param num_groups: the number of groups to be created

    """
    # TODO pass in the name of the group

    logger.info('reset_owncloud_group for group: %s', config.oc_group_name)

    if num_groups is None:
        num_groups = config.oc_number_test_groups

    for i in range(1, num_groups + 1):
        group_name = "%s%i" % (config.oc_group_name, i)
        delete_owncloud_group(group_name)
        create_owncloud_group(group_name)


def check_owncloud_group(group_name):
    """ Checks if a group exists on the server

    :param group_name: name of the group to be checked

    """
    logger.info('Checking if group %s exists', group_name)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    exists = oc_api.group_exists(group_name)
    return exists


def delete_owncloud_group(group_name):
    """ Deletes a group on the server

    :param group_name: name of the group to be deleted

    """
    logger.info('Deleting group %s', group_name)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    oc_api.delete_group(group_name)


def create_owncloud_group(group_name):
    """ Creates a group on the server

    :param group_name: name of the group to be created

    """
    logger.info('Creating group %s', group_name)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    oc_api.create_group(group_name)


######### WEBDAV AND SYNC UTILITIES #####################

def oc_webdav_url(protocol='http',remote_folder="",user_num=None,webdav_endpoint=None,hide_password=False):
    """ Protocol for sync client should be set to 'owncloud'. Protocol for generic webdav clients is http.
    """

    if config.oc_ssl_enabled:
        protocol += 's'

    if webdav_endpoint is None:
        webdav_endpoint = config.oc_webdav_endpoint

    # strip off any leading/trailing slashes so that remote path does not start or end with / nor it contains double //
    remote_path = "/".join([p.strip('/') for p in [webdav_endpoint, config.oc_server_folder, remote_folder]])

    remote_path = remote_path.strip('/')

    if user_num is None:
        username = "%s" % config.oc_account_name
    else:
        username = "%s%i" % (config.oc_account_name, user_num)

    if hide_password:
        password = "***"
    else:
        password = config.oc_account_password

    return protocol + '://' + urllib.quote(username, safe='') + ':' + urllib.quote(password, safe='') + '@' + config.oc_server + '/' + remote_path


def ocsync_version():
    """ Return the version reported by oc_sync_cmd.

    Returns a tuple (major,minor,bugfix). For example: (1,7,2) or (2,1,1)
    """

    # strip possible options from config.oc_sync_cmd
    cmd = config.oc_sync_cmd.split()[0] + " --version"
    rc,stdout,stderr = runcmd(cmd, ignore_exitcode=True,log_warning=False) # do not warn about non-zero exit code (which is unfortunately normal)

    sver = stdout.strip().split()[-1] # the version is the last word on the first line
    
    return tuple([int(x) for x in sver.split(".")])

# this is a local variable for each worker that keeps track of the repeat count for the current step
ocsync_cnt = {}


def run_ocsync(local_folder, remote_folder="", n=None, user_num=None):
    """ Run the ocsync for local_folder against remote_folder (or the main folder on the owncloud account if remote_folder is None).
    Repeat the sync n times. If n given then n -> config.oc_sync_repeat (default 1).
    """
    global ocsync_cnt
    from smashbox.utilities import reflection

    if n is None:
        n = config.oc_sync_repeat

    current_step = reflection.getCurrentStep()

    ocsync_cnt.setdefault(current_step,0)

    if platform.system() != "Windows":
        local_folder += os.sep # FIXME: HACK - is a trailing slash really needed by 1.6 owncloudcmd client?

    for i in range(n):
        t0 = datetime.datetime.now()
        cmd = config.oc_sync_cmd+[local_folder,oc_webdav_url('owncloud',remote_folder,user_num)]
        logf = file(os.path.join(config.rundir,"%s-ocsync.step%02d.cnt%03d.log"%(reflection.getProcessName(),current_step,ocsync_cnt[current_step])),"wb")

        logger.info('sync cmd is: %s',repr(cmd))

        process = subprocess.Popen(cmd, shell=False, stdout=logf, stderr=subprocess.STDOUT)
        process.communicate()

        if process.returncode != 0:
            msg = "Non-zero exit code %d from command %s" % (process.returncode, repr(cmd))
            logger.warning(msg)

        logger.info('sync finished: %s',datetime.datetime.now()-t0)
        ocsync_cnt[current_step]+=1

def _prop_check(path,user_num=None,depth="0"):
    """ Private function to implement other utilities.
    """
    import smashbox.curl
    c = smashbox.curl.Client()
    url = oc_webdav_url(remote_folder=path, user_num=user_num)
    query = """<?xml version="1.0" encoding="UTF-8"?><D:propfind xmlns:D="DAV:"><D:allprop/></D:propfind>"""

    r = c.PROPFIND(url,query,depth=depth)
    return r



def webdav_propfind_ls(path, user_num=None):
    import xml.dom.minidom
    r = _prop_check(path,user_num,depth="1")
    x=xml.dom.minidom.parseString(r.response_body)
    logger.info('Listing %s by PROPFIND: %s'%(repr(path),x.toprettyxml()))

def expect_webdav_does_not_exist(path, user_num=None):

    r = _prop_check(path,user_num)
    error_check(r.rc >= 400,"Remote path exists: %s" % path) # class 4xx response is OK

def expect_webdav_exist(path, user_num=None):

    r = _prop_check(path,user_num)
    error_check(200 <= r.rc and r.rc < 300,"Remote path does not exist: %s" % path) # class 2xx response is OK


# The two functions implementations below with pycurl currently fail with:
# * warning: ignoring value of ssl.verifyhost
# * NSS error -8023
# * Closing connection #0
# * SSL connect error

def webdav_delete(path, silent=True, user_num=None):

    # work around buggy pycurl.so on MacOSX...
    if platform.system() == "Darwin":
        import logging
        if config._loglevel <= logging.DEBUG:
            verbose = "--verbose"
            echo=True
        else:
            verbose = ""
            echo=False
        runcmd('curl %s -k %s -X DELETE %s '%(verbose,config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num)),echo=echo)
    else:
        import smashbox.curl
        c = smashbox.curl.Client(verbose=not silent) # FIXME: handle config.get('curl_opts','')
        url = oc_webdav_url(remote_folder=path, user_num=user_num)
        return c.DELETE(url)
    
def webdav_mkcol(path, silent=True, user_num=None):

    # work around buggy pycurl.so on MacOSX...
    if platform.system() == "Darwin":
        out=""
        import logging
        if silent or config._loglevel > logging.DEBUG: # a workaround for super-verbose errors in case directory on the server already exists
            out = "> /dev/null 2>&1"
            echo=False
        else:
            echo=True
        runcmd('curl --verbose -k %s -X MKCOL %s %s'%(config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num),out),echo=echo)
    else:
        import smashbox.curl
        c = smashbox.curl.Client(verbose=not silent) 
        url = oc_webdav_url(remote_folder=path, user_num=user_num)
        return c.MKCOL(url)

###############

# #### SHELL COMMANDS AND TIME FUNCTIONS

def runcmd(cmd,ignore_exitcode=False,echo=True,allow_stderr=True,shell=True,log_warning=True):
    logger.info('running %s', repr(cmd))

    process = subprocess.Popen(cmd, shell=shell,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = process.communicate()

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
        if log_warning:
            logger.warning(msg)
        if not ignore_exitcode:
            raise subprocess.CalledProcessError(process.returncode,cmd)

    return (process.returncode, stdout, stderr)


def sleep(n):
    logger.info('sleeping %s seconds',n)
    time.sleep(n)


######## BASIC FILE AND DIRECTORY OPERATIONS

def mkdir(d):
    logger.info('mkdir %s',d)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def remove_tree(path):
    logger.info('remove directory tree %s',path)
    shutil.rmtree(path)


def remove_file(path):
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
    logger.info("move %s %s",a,b)
    shutil.move(a, b)


def list_files(path,recursive=False):

    if platform.system() == 'Windows':
        runcmd('dir /s /b ' + path)
        return
 
    if platform.system() == 'Darwin':
        opts = ""
    else:
        opts = "--full-time"

    if recursive:
        runcmd('ls -lR %s %s'%(opts,path))
    else:
        runcmd('ls -lh %s %s'%(opts,path))

#http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python#377028
    
def is_exe(fpath):
    import os
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

def which(program):
    import os
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


# ## DATA FILES AND VERSIONS

def createfile(fn,c,count,bs):
    # this replaces the dd as 1) more portable, 2) not prone to problems with escaping funny filenames in shell commands
    logger.info('createfile %s character=%s count=%d bs=%d',fn,repr(c),count,bs)
    buf = c*bs
    of = file(fn,'w')
    for i in range(count):
        of.write(buf)
    of.close()


def modify_file(fn,c,count,bs):
    logger.info('modify_file %s character=%s count=%d bs=%d',fn,repr(c),count,bs)
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

    of = open(fn, 'a')
    of.seek(0,2)
    for i in range(count):
        logger.info('modify_file: appending ')
        of.write(buf)
    of.close()


def delete_file(fn):
    logger.info('delete_file: deleting file %s ',fn)
    if os.path.exists(fn):
        os.remove(fn)


def createfile_zero(fn,count,bs):
    createfile(fn,'\0',count,bs)

# some tests depend on md5sum in this module
# use portable implementation of md5sum
def md5sum(fn):
    from hash_files import md5sum as _md5sum
    return _md5sum(fn)

def hexdump(fn):
    if platform.system() == "Windows":
        # FIXME: this implementation is missing some formatting features of hexdump:
        # byte offset column and spacing between bytes
        with open(fn, 'rb') as f:
            for chunk in iter(lambda: f.read(32), b''):
                chunk.encode('hex')
    else:
        runcmd('hexdump %s'%fn)


def list_versions_on_server(fn):
    cmd = "%(oc_server_shell_cmd)s md5sum %(oc_server_datadirectory)s/%(oc_account_name)s/files_versions/%(filename)s.v*" % config._dict(filename=os.path.join(config.oc_server_folder, os.path.basename(fn)))  # PENDING: bash -x 
    runcmd(cmd)


def hexdump_versions_on_server(fn):
    cmd = "%(oc_server_shell_cmd)s hexdump %(oc_server_datadirectory)s/%(oc_account_name)s/files_versions/%(filename)s.v*" % config._dict(filename=os.path.join(config.oc_server_folder, os.path.basename(fn)))  # PENDING: bash -x 
    runcmd(cmd)


def get_md5_versions_on_server(fn):
    cmd = "%(oc_server_shell_cmd)s md5sum %(oc_server_datadirectory)s/%(oc_account_name)s/files_versions/%(filename)s.v*" % config._dict(filename=os.path.join(config.oc_server_folder, os.path.basename(fn)))

    logger.info('running %s',repr(cmd))
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)

    stdout=process.communicate()[0]

    result=[]
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        md,fn = line.split()
        result.append((md,os.path.basename(fn)))
        #log(result[-1])

    return result


# ###### LOGIC OPERANDS  ############

def implies(p,q):
    return not p or q

# ###### ERROR REPORTING ############

reported_errors = []

def error_check(expr,message=""):
    """ Assert expr is True. If not, then mark the test as failed but carry on the execution.
    """

    if not expr: 
        import inspect
        f=inspect.getouterframes(inspect.currentframe())[1]
        message=" ".join([message, "%s failed in %s() [\"%s\" at line %s]" %(''.join(f[4]).strip(),f[3],f[1],f[2])])
        logger.error(message)
        reported_errors.append(message)

def fatal_check(expr,message=""):
    """ Assert expr is True. If not, then mark the test as failed and stop immediately.
    """
    if not expr:
        import inspect
        f=inspect.getouterframes(inspect.currentframe())[1]
        message=" ".join([message, "%s failed in %s() [\"%s\" at line %s]" %(''.join(f[4]).strip(),f[3],f[1],f[2])])
        logger.fatal(message)
        reported_errors.append(message)
        raise AssertionError(message)


# ###### Server Log File Scraping ############

def reset_server_log_file():
    """ Deletes the existing server log file so that there is a clean
        log file for the test run
    """

    try:
        if not config.oc_check_server_log:
            return
    except AttributeError: # allow this option not to be defined at all
        return

    logger.info('Removing existing server log file')
    cmd = '%s rm -rf %s/owncloud.log' % (config.oc_server_shell_cmd, config.oc_server_datadirectory)
    runcmd(cmd)



def scrape_log_file(d):
    """ Copies over the server log file and searches it for specific strings

    :param d: The directory where the server log file is to be copied to

    """

    try:
        if not config.oc_check_server_log:
            return
    except AttributeError: # allow this option not to be defined at all
        return

    if config.oc_server == '127.0.0.1' or config.oc_server == 'localhost':
        cmd = 'cp %s/owncloud.log %s/.' % (config.oc_server_datadirectory, d)
    else:
        try:
            log_user = config.oc_server_log_user
        except AttributeError:  # allow this option not to be defined at all
            log_user = 'root'
        cmd = 'scp -P %d %s@%s:%s/owncloud.log %s/.' % (config.scp_port, log_user, config.oc_server, config.oc_server_datadirectory, d)
    rtn_code,stdout,stderr = runcmd(cmd)
    error_check(rtn_code > 0, 'Could not copy the log file from the server, command returned %s' % rtn_code)

    # search logfile for string (1 == not found; 0 == found):
    cmd = "grep -i \"integrity constraint violation\" %s/owncloud.log" % d
    rtn_code,stdout,stderr = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Integrity Constraint Violation\" message found in server log file")

    cmd = "grep -i \"Exception\" %s/owncloud.log" % d
    rtn_code,stdout,stderr = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Exception\" message found in server log file")

    cmd = "grep -i \"could not obtain lock\" %s/owncloud.log" % d
    rtn_code,stdout,stderr = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Could Not Obtain Lock\" message found in server log file")

    cmd = "grep -i \"db error\" %s/owncloud.log" % d
    rtn_code,stdout,stderr = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"DB Error\" message found in server log file")

    cmd = "grep -i \"stat failed\" %s/owncloud.log" % d
    rtn_code,stdout,stderr = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Stat Failed\" message found in server log file")


# ###### API Calls ############

def get_oc_api():
    """ Returns an instance of the Client class

    :returns: Client instance
    """
    import owncloud

    protocol = 'http'
    if config.oc_ssl_enabled:
        protocol += 's'

    url = protocol + '://' + config.oc_server + '/' + config.oc_root
    oc_api = owncloud.Client(url, verify_certs=False)
    return oc_api


def share_file_with_user(filename, sharer, sharee, **kwargs):
    """ Shares a file with a user

    :param filename: name of the file being shared
    :param sharer: the user doing the sharing
    :param sharee: the user receiving the share
    :param kwargs: key words args to be passed into the api, usually for share permissions
    :returns: share id of the created share

    """
    from owncloud import ResponseError

    logger.info('%s is sharing file %s with user %s', sharer, filename, sharee)

    oc_api = get_oc_api()
    oc_api.login(sharer, config.oc_account_password)

    try:
        share_info = oc_api.share_file_with_user(filename, sharee, **kwargs)
        logger.info('share id for file share is %s', str(share_info.share_id))
        return share_info.share_id
    except ResponseError as err:
        logger.info('Share failed with %s', str(err))
        if "not allowed to share" in str(err.get_resource_body()):
            return -1
        else:
            return -2


def delete_share(sharer, share_id):
    """ Deletes a share

    :param sharer: user who created the original share
    :param share_id: id of the share to be deleted

    """
    logger.info('Deleting share %i from user %s', share_id, sharer)

    oc_api = get_oc_api()
    oc_api.login(sharer, config.oc_account_password)
    oc_api.delete_share(share_id)


def share_file_with_group(filename, sharer, group, **kwargs):
    """ Shares a file with a group

    :param filename: name of the file being shared
    :param sharer: the user doing the sharing
    :param group: the group receiving the share
    :param kwargs: key words args to be passed into the api, usually for share permissions
    :returns: share id of the created share

    """
    logger.info('%s is sharing file %s with group %s', sharer, filename, group)

    oc_api = get_oc_api()
    oc_api.login(sharer, config.oc_account_password)
    groupshare_info = oc_api.share_file_with_group(filename, group, **kwargs)

    logger.info('share id for file group share is %i', groupshare_info.share_id)
    return groupshare_info.share_id


def add_user_to_group(username, group_name):
    """ Adds a user to a group

    :param username: name of user to be added to the group
    :param group_name: name of group the user is being added to
    """
    logger.info('Adding user %s to group %s', username, group_name)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    oc_api.add_user_to_group(username, group_name)


def remove_user_from_group(username, group_name):
    """ Removes a user from a group

    :param username: name of user to be removed from the group
    :param group_name: name of group the user is being removed from
    """
    logger.info('Removing user %s from group %s', username, group_name)

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    oc_api.remove_user_from_group(username, group_name)


def check_users(num_test_users=None):
    """ Checks if a user(s) exists or not
    """
    result = check_owncloud_account(config.oc_account_name)
    fatal_check(result, 'User %s not found' % config.oc_account_name)

    if num_test_users is not None:
        for i in range(1, num_test_users + 1):
            username = "%s%i" % (config.oc_account_name, i)
            result = check_owncloud_account(username)
            fatal_check(result, 'User %s not found' % username)


def check_groups(num_groups=None):
    """ Checks if a group exists or not
    """
    if num_groups is None:
        result = check_owncloud_group(config.oc_group_name)
        fatal_check(result, 'Group %s not found' % config.oc_group_name)
    else:
        for i in range(1, num_groups + 1):
            group_name = "%s%i" % (config.oc_group_name, i)
            result = check_owncloud_group(group_name)
            fatal_check(result, 'Group %s not found' % group_name)


def expect_modified(fn, md5, comment=''):
    """ Compares that the checksum of two files is different
    """
    actual_md5 = md5sum(fn)
    error_check(actual_md5 != md5,
                "md5 of modified file %s did not change%s: expected %s" % (fn, comment, md5))


def expect_not_modified(fn, md5, comment=''):
    """ Compares that the checksum of two files is the same
    """
    actual_md5 = md5sum(fn)
    error_check(actual_md5 == md5,
                "md5 of modified file %s changed%s and should not have: expected %s, got %s" % (fn, comment, md5, actual_md5))


def expect_exists(fn):
    """ Checks that a files exists as expected
    """
    error_check(os.path.exists(fn), "File %s does not exist but should" % fn)


def expect_does_not_exist(fn):
    """ Checks that a file does not exist, as expected
    """
    error_check(not os.path.exists(fn), "File %s exists but should not" % fn)

