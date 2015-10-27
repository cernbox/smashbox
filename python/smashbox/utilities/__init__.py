from smashbox.script import config

import os.path
import datetime
import subprocess
import time

# Utilities to be used in the test-cases.

def OWNCLOUD_CHUNK_SIZE(factor=1):
    """Calculate file size as a fraction of owncloud client's default chunk size.
    """
    return int(20*1024*1024*factor) # 20MB as of client 1.7 


######## TEST SETUP AND PREPARATION

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
    
    elif reset_procedure == 'webdav_delete':
        webdav_delete('/') # delete the complete webdav endpoint associated with the remote account
        webdav_delete('/') # FIXME: workaround current bug in EOS (https://savannah.cern.ch/bugs/index.php?104661) 
        webdav_mkcol('/')
        
    # if create if does not exist (for keep or webdav_delete options)


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

    # strip-off any leading / characters to prevent 1) abspath result from the join below, 2) double // and alike...
    remote_folder = remote_folder.lstrip('/')

    if webdav_endpoint is None:
        webdav_endpoint = config.oc_webdav_endpoint

    remote_path = os.path.join(webdav_endpoint, config.oc_server_folder, remote_folder)

    if user_num is None:
        username = "%s" % config.oc_account_name
    else:
        username = "%s%i" % (config.oc_account_name, user_num)

    if hide_password:
        password = "***"
    else:
        password = config.oc_account_password
        
    import urllib    
    username = urllib.quote(username.encode("utf-8"))
    password = urllib.quote(password.encode("utf-8"))   
    oc_server = urllib.quote((config.oc_server).encode("utf-8"))  
    
    return protocol + '://' + username + ':' + password + '@' + config.oc_server + '/' + remote_path


# this is a local variable for each worker that keeps track of the repeat count for the current step
ocsync_cnt = {}

sync_exec_time_array = []

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

    local_folder += '/' # FIXME: HACK - is a trailing slash really needed by 1.6 owncloudcmd client?

    for i in range(n):
        t0 = datetime.datetime.now()
        cmd = config.oc_sync_cmd+' '+local_folder+' '+oc_webdav_url('owncloud',remote_folder,user_num) + " >> "+config.rundir+"/%s-ocsync.step%02d.cnt%03d.log 2>&1"%(reflection.getProcessName(),current_step,ocsync_cnt[current_step])
        runcmd(cmd, ignore_exitcode=True)  # exitcode of ocsync is not reliable
        sync_exec_time = (datetime.datetime.now()-t0).total_seconds() 
        sync_exec_time_array.append(sync_exec_time)  
        logger.info('sync cmd is: %s',cmd)
        logger.info('sync finished: %s s',sync_exec_time)
        ocsync_cnt[current_step]+=1  

def webdav_propfind_ls(path, user_num=None):
    runcmd('curl -s -k %s -XPROPFIND %s | xmllint --format -'%(config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num)))

def expect_webdav_does_not_exist(path, user_num=None):
    exitcode,stdout,stderr = runcmd('curl -s -k %s -XPROPFIND %s | xmllint --format - | grep NotFound | wc -l'%(config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num)))
    not_exists = stdout.rstrip() == "1"
    error_check(not_exists, "Remote path does not %s exist but should" % path)

def expect_webdav_exist(path, user_num=None):
    exitcode,stdout,stderr = runcmd('curl -s -k %s -XPROPFIND %s | xmllint --format - | grep NotFound | wc -l'%(config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num)))
    exists = stdout.rstrip() == "0"
    error_check(exists, "Remote path %s exists but should not" % path)

def webdav_delete(path, user_num=None):
    runcmd('curl -k %s -X DELETE %s '%(config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num)))

def webdav_mkcol(path, silent=False, user_num=None):
    out=""
    if silent: # a workaround for super-verbose errors in case directory on the server already exists
        out = "> /dev/null 2>&1"
    runcmd('curl -k %s -X MKCOL %s %s'%(config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num),out))

# #### SHELL COMMANDS AND TIME FUNCTIONS

reported_errors = []

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
        msg = "Non-zero exit code %d from command %s" % (ignore_exitcode,repr(cmd))
        if log_warning:
            reported_errors.append(msg)
            logger.warning(msg)
        if not ignore_exitcode:
            raise subprocess.CalledProcessError(process.returncode,cmd)

    return (process.returncode, stdout, stderr)


def sleep(n):
    logger.info('sleeping %s seconds',n)
    time.sleep(n)


######## BASIC FILE AND DIRECTORY OPERATIONS

def mkdir(d):
    runcmd('mkdir -p '+d)
    return d


def remove_tree(path):
    runcmd('rm -rf '+path)


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
    runcmd('mv %s %s'%(a,b))


def list_files(path,recursive=False):
    if recursive:
        runcmd('ls -lR --full-time %s'%path)
    else:
        runcmd('ls -lh --full-time %s'%path)


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


import platform

if platform.system() == 'Darwin':

    def md5sum(fn):
        process = subprocess.Popen('md5 %s'%fn,shell=True,stdout=subprocess.PIPE)
        out = process.communicate()[0]
        try:
            return out.split()[-1]
        except IndexError:
            return "NO_CHECKSUM_ERROR"

else:  # linux

    def md5sum(fn):
        process=subprocess.Popen('md5sum %s'%fn,shell=True,stdout=subprocess.PIPE)
        out = process.communicate()[0]
        try:
            return out.split()[0]
        except IndexError:
            return "NO_CHECKSUM_ERROR"


def hexdump(fn):
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

def scrape_log_file(d):
    """ Copies over the server log file and searches it for specific strings

    :param d: The directory where the server log file is to be copied to

    """
    cmd = 'scp -P %d root@%s:%s/owncloud.log %s/.' % (config.scp_port, config.oc_server, config.oc_server_datadirectory, d)
    rtn_code,stdout,stderr = runcmd(cmd)

    logger.info('copy command returned %s', rtn_code)

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

            
def curl_check_url(config):
    from smashbox.utilities import  oc_webdav_url
    import smashbox.curl, sys
    
    url = oc_webdav_url(remote_folder='', user_num=None)
    query="""<?xml version="1.0" ?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
  </d:prop>
</d:propfind>
"""
    client = smashbox.curl.Client()
    exit_flag = False
    try:
        r = client.PROPFIND(url,query,depth=0,parse_check=False)
        if r.body_stream.getvalue() == "":
            print ("\n%s\n\nSMASHBOX_CHECK ERROR: %s, Empty response\nCHECK CONFIGURATION - oc_root, oc_ssl_enabled, oc_server, oc_server_shell_cmd etc.\nCHECK HEADERS e.g. for 302 - Location=%s\n"%(r.headers,r.rc,str(r.headers['Location'])))
            exit_flag = True
        else:
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(r.body_stream.getvalue())
                if root.tag.find("error") != -1:
                    raise Exception
                else:
                    print "SMASHBOX_CHECK OK"
            except:
                print "SMASHBOX_CHECK ERROR: %s"%r.body_stream.getvalue()  
                exit_flag = True
    except Exception, e:
        exit_flag = True
        print e
    finally:
        if(exit_flag):
            sys.exit() 