from smashbox.script import config

import os.path
import datetime
import subprocess,signal
import time
# Utilities to be used in the test-cases.

def OWNCLOUD_CHUNK_SIZE(factor=1):
    """Calculate file size as a fraction of owncloud client's default chunk size.
    """
    return int(20*1024*1024*factor) # 20MB as of client 1.7 

test_reporter = None

def setup_test(_smash_,manager):
    """ Setup hooks run before any worker kicks-in. 
    This is run under the name of the "supervisor" worker.

    The behaviour of these hooks is entirely controlled by config
    options. It should be possible to disable optional hooks by
    configuration.

    If exception is raised then the testcase execution is aborted and smashbox terminates with non-zero exit code,

    """
    import imp,sys
    global test_reporter
    #check prerequisites
    try:
        imp.find_module('numpy')
        imp.find_module('netifaces')
        imp.find_module('pycurl')
    except ImportError,e:
        logger.error(e) 
        sys.exit()
    
    try:
        import smashbox.test_reporter
        test_reporter = smashbox.test_reporter.Test_Reporter(os.path.basename(_smash_.args.test_target),config,_smash_.workers,manager)
    except:
        pass
    
    #initialize the synchronisation client
    sync_client_start(_smash_)  
    
def finalize_test():
    """ Finalize hooks run after last worker terminated.
    This is run under the name of the "supervisor" worker.

    The behaviour of these hooks is entirely controlled by config
    options. It should be possible to disable optional hooks by
    configuration.
    
    If exception is raised then smashbox terminates with non-zero exit code,
    """
    global test_reporter
    try:
        test_reporter.finalize_test()
    except:
        pass
    d = make_workdir()
    scrape_log_file(d)
    
    sync_client_stop()  

def finalize_step():
    """ Finalize hooks run after each step run.
    This is run under the name of the "supervisor" worker.

    The behaviour of these hooks is entirely controlled by config
    options. It should be possible to disable optional hooks by
    configuration.
    
    If exception is raised then smashbox terminates with non-zero exit code,
    """
    global test_reporter
    try:
        test_reporter.finalize_step()
    except:
        pass
    
    sync_client_step()  

def finalize_worker(fname):   
    """ Finalize hooks run after each worker terminated.
    This is run under the name of the "supervisor" worker.

    The behaviour of these hooks is entirely controlled by config
    options. It should be possible to disable optional hooks by
    configuration.
    
    If exception is raised then smashbox terminates with non-zero exit code,
    """
    global test_reporter
    try:
        test_reporter.finalize_worker(sync_exec_time_array, reported_errors,fname)
    except:
        pass
         
    if reported_errors:
        logger.error('%s error(s) reported',len(reported_errors))
        import sys
        sys.exit(2)
        
    sync_client_finish()  
######### HELPERS
######## TEST SETUP AND PREPARATION

# this is a local variable for each worker that keeps track of the repeat count for the current step
ocsync_cnt = {}
sync_exec_time_array = []
reported_errors = []

def run_ocsync(local_folder, remote_folder="", n=None, user_num=None, option = []):
    """ Run the ocsync for local_folder against remote_folder (or the main folder on the owncloud account if remote_folder is None).
    Repeat the sync n times. If n given then n -> config.oc_sync_repeat (default 1).
    """
    global ocsync_cnt
    from smashbox.utilities import reflection

    if n is None:
        n = config.oc_sync_repeat

    current_step = reflection.getCurrentStep()

    ocsync_cnt.setdefault(current_step,0)

    for i in range(n):
        log_location = config.rundir+"/%s-ocsync.step%02d.cnt%03d.log"%(reflection.getProcessName(),current_step,ocsync_cnt[current_step])
        sync_exec_time_pair,sync_exec_time = sync_engine(log_location, local_folder, remote_folder, user_num,option) 
        
        logger.info('sync finished: %s s'%(sync_exec_time))
        
        sync_exec_time_array.append(sync_exec_time_pair) 
        ocsync_cnt[current_step]+=1

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
    if platform.system() == 'Darwin':
        opts = ""
    else:
        opts = "--full-time"

    if recursive:
        runcmd('ls -lR %s %s'%(opts,path))
    else:
        runcmd('ls -lh %s %s'%(opts,path))


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

def create_dummy_file(wdir,name,size,bs=None):
    """ by default - creates file with fully random content, specified name and in specific directory. 
    By specifing bs blocksize, random bytes will be structured in blocks and repeated ntimes """
    import random
    nbytes = int(size)
    
    if bs is None:
        bs = nbytes

    nblocks = nbytes/bs
    nr = nbytes%bs
          
    assert nblocks*bs+nr==nbytes,'Chunking error!'

    time.sleep(0.1)

    # Prepare the building blocks
    fn = os.path.join(wdir,name)

    f = file(fn,'w')

    block_data = str(os.urandom(bs)) # Repeated nblocks times
    # write data blocks
    for i in range(nblocks):
        f.write(block_data)

    block_data_r = str(os.urandom(nr))       # Only once
    f.write(block_data_r)
    f.close()

    return fn

def modify_dummy_file(fn,size,bs=None,checksum=False):
    import random
    import hashlib
    
    nbytes = int(size)
    
    if bs is None:
        bs = nbytes
        
    nblocks = nbytes/bs
    nr = nbytes%bs

    assert nblocks*bs+nr==nbytes,'Chunking error!'

    time.sleep(0.1)

    # Prepare the building blocks
    f = file(fn,'a')
    f.seek(0,2)
    # write data blocks
    for i in range(nblocks):
        block_data = str(os.urandom(bs)) # Repeated nblocks times
        f.write(block_data)

    block_data_r = str(os.urandom(nr))       # Only once
    f.write(block_data_r)
    f.close()
    if checksum==True:
        f = file(fn,'r')
        data = f.read()
        f.close()
        md5 = hashlib.md5()
        md5.update(data)
        filemask = "{md5}"        
        new_fn = os.path.join(os.path.dirname(fn),filemask.replace('{md5}',md5.hexdigest()))
        os.rename(fn,new_fn)
                
def stop_execution(pid):      
    pid = int(pid)
    print ("killing %s: ok"%pid)
    try:
        os.killpg(pid, signal.SIGTERM)
        time.sleep(2)
        try:
            os.killpg(pid, signal.SIGKILL)
        except:
            pass
        time.sleep(2)
    except Exception, e:
        print (e)
        print "dirty kill.."
        subprocess.call("kill -TERM %s"%pid, shell=True)
        
                    
""" This section defines the functions which could be overwriten by more than one sync client 
    implementations in order to perform scenario not dependent on the synchronisation client """
sync_client = None      
def engine_dependence(func):
    """Decorator for client dependent functions """
    def checker(*args, **kwargs): 
        try:
            #check if there was specified any additional engine using e.g. --option engine=dropbox
            global sync_client
            if sync_client is None and hasattr(config, "engine"):
                sync_client = globals()[config.engine]()
            elif sync_client is None:
                sync_client = globals()["owncloud"]()
                        
            return getattr(sync_client, func.__name__)(args,kwargs) #print "executing sync engine custom function %s"%func.__name__
        except Exception, e:
            logger.error(e)
            return func(*args, **kwargs) #
    return checker 
 
@engine_dependence
def sync_client_start():
    pass

@engine_dependence
def sync_client_finish():
    pass

@engine_dependence
def sync_client_step():
    pass

@engine_dependence
def sync_client_stop():
    pass

@engine_dependence
def make_workdir():
    pass

@engine_dependence
def oc_webdav_url():
    pass        

@engine_dependence
def sync_engine():
    pass     

""" owncloud section """                   
class owncloud:
    def __init__(self):
        pass
    
    @staticmethod   
    def sync_client_start(args,kwargs):
        check_settings()
        reset_owncloud_account(num_test_users=config.oc_number_test_users)
        reset_rundir()
        reset_server_log_file()
        
    @staticmethod
    def sync_client_finish(args,kwargs):
        pass
    
    @staticmethod
    def sync_client_step(args,kwargs):
        pass
    
    @staticmethod
    def sync_client_stop(args,kwargs):
        pass    
    
    @staticmethod      
    def sync_engine(args,kwargs):
        """ log_location is args[0], local_folder is args[1], remote_folder is args[2], 
            user_num is args[3], options are args[4] """
        cmd = config.oc_sync_cmd+' '+args[1]+' '+oc_webdav_url('owncloud',args[2],args[3])
        #defult ownCloud sync engine
        cmd = cmd + " >> "+ args[0] + " 2>&1" 
        t0 = datetime.datetime.now()
        runcmd(cmd, ignore_exitcode=True)  # exitcode of ocsync is not reliable
        t1 = datetime.datetime.now()
        logger.info('sync cmd is: %s',cmd) 
        
        sync_exec_time_pair=[t0,t1]
        for opt in args[4]:
            if opt=='exclude_time':
                sync_exec_time_pair=None
        return sync_exec_time_pair,t1-t0
    
    @staticmethod   
    def oc_webdav_url(args,kwargs):
        """ Protocol for sync client should be set to 'owncloud'. Protocol for generic webdav clients is http.
        """
        protocol = 'http'
        remote_folder= ""
        user_num = None
        webdav_endpoint = config.oc_webdav_endpoint
        hide_password= False
        
        for key, value in kwargs.iteritems():
            if key=='protocol':
                protocol = value
            elif key=='remote_folder':
                # strip-off any leading / characters to prevent 1) abspath result from the join below, 2) double // and alike...
                remote_folder = value
                remote_folder = remote_folder.lstrip('/')
            elif key=='user_num':
                user_num = value
            elif key=='webdav_endpoint':
                webdav_endpoint = value
            elif key=='hide_password':
                hide_password = value
        
        if config.oc_ssl_enabled:
            protocol += 's'
    
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
    
        return protocol + '://' + username + ':' + password + '@' + config.oc_server + '/' + remote_path
    
    @staticmethod 
    def make_workdir(args,kwargs):
        """ Create a worker directory in the current run directory for the test (by default the name is derived from 
        the worker's name). 
        """
        name = None
        
        for key, value in kwargs.iteritems():
            if key=='name':
                name = value
                
        if name is None:
            name = reflection.getProcessName()
    
        d = os.path.join(config.rundir,name)
        mkdir(d)
        logger.info('make_workdir %s',d)
        return d
    
    @staticmethod
    def hello():
        print "Hello world!"
        
    @staticmethod
    def stop(pid):
        print "Stopping..",pid
        stop_execution(pid)
        
""" owncloud utilities """

def check_settings():
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
            except:
                print "SMASHBOX_CHECK ERROR: %s"%r.body_stream.getvalue()  
                if str(r.body_stream.getvalue()).find("HTML") != -1:
                    exit_flag=False
                else:
                    exit_flag = True
    except Exception, e:
        exit_flag = True
        print "Error!",e
    finally:
        if(exit_flag):
            sys.exit()     


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

""" dropbox section """                   
class dropbox:
    def __init__(self):
        pass
    
    @staticmethod   
    def sync_client_start(args,kwargs):
        smash_workers = args[0].workers
        smashdir = config.smashdir
        install_dropbox()
        check_if_dropbox_stopped()
        boss="boss"
        clean_directory(smashdir, boss)
        import time
        time.sleep(1)
        start_dropbox(boss, smashdir) 
        if(get_running_dropbox(boss, smashdir) != None):
            clean_directory(smashdir, boss)
            import time
            time.sleep(1)
        
        worker_name_array = []   
        if(get_running_dropbox(boss, smashdir) != None):
            for i,f_n in enumerate(smash_workers):
                f = f_n[0]
                fname = f_n[1]
                if fname is None:
                    fname = f.__name__ 
                worker_name_array.append(fname) 
                dropbox_add_workers_to_conf(fname, smashdir)   
            prepare_smashbox(smashdir,worker_name_array,boss)
                
    @staticmethod
    def sync_client_finish(args,kwargs):
        pass
    
    @staticmethod
    def sync_client_step(args,kwargs):
        check_if_stopped("dropbox")
    
    @staticmethod
    def sync_client_stop(args,kwargs):
        print "START FINISHING DROPBOX"
        check_if_dropbox_stopped()    
    
    @staticmethod      
    def sync_engine(args,kwargs):
        """ log_location is args[0], local_folder is args[1], remote_folder is args[2], 
            user_num is args[3], options are args[4] """
        worker_name = reflection.getProcessName()
        options = args[4]
        stop = True
        finish = False
        exclude = False
        if options:
            for opt in options:
                if opt=='exclude_time':
                    exclude = True
                elif opt=='start_only':
                    stop = False
                elif opt=='finish_only':
                    finish = True
        local_folder = os.path.abspath(os.path.join(config.smashdir,"dropbox-"+worker_name+"/Dropbox/"))
        if finish==False:
            dropbox_restart(config.smashdir, worker_name, local_folder)
        t0 = datetime.datetime.now()
        log = get_running_dropbox(worker_name, config.smashdir)
        if(log != None):
            result = [t0,datetime.datetime.now()]
            sync_exec_time = result[1]-result[0]
            if stop==True:
                stop_dropbox(worker_name, config.smashdir)  
            if exclude==True:
                return None,sync_exec_time
            log_test(args[0],log)
            return result,sync_exec_time
    
    @staticmethod   
    def oc_webdav_url(args,kwargs):
        return "dropbox"
    
    @staticmethod 
    def make_workdir(args,kwargs):
        name = None
        for key, value in kwargs.iteritems():
            if key=='name':
                name = value
        if name is None:
            name = reflection.getProcessName()
            
        d = os.path.abspath(os.path.join(config.smashdir,"dropbox-"+name+"/Dropbox"))
        return d
    
    @staticmethod
    def hello():
        print "Hello world!"
        
    @staticmethod
    def stop(pid):
        print "Stopping..",pid
        kill_if_not_stopped("dropbox")
        stop_execution(pid)
        
""" dropbox utilities """

def install_dropbox():
    from os.path import expanduser
    import platform,sys
    def is_32bit():
        if (platform.architecture()[0]).find("64") != -1:
            return "x86_64"
        else:
            return "x86"
    home = expanduser("~")
    directory = home + "/.dropbox-dist"
    if not os.path.exists(directory):
        print "%s does not exists, begin installation.."%directory
        dist = 'http://www.dropbox.com/download/?plat=lnx.%s'%is_32bit()
        import subprocess
        subprocess.call(["wget", "-O", "dropbox.tar.gz",dist], cwd=home)
        print "downloaded, unpack"
        subprocess.call(["tar", "-xvzf", "dropbox.tar.gz"], cwd=home)
    print "dropbox installed"

def check_if_dropbox_stopped():
    import time
    t_syncprepare = time_now() 
    running = True
    cmd = os.path.dirname(__file__)+"/running.sh dropbox"
    status = "Process not running"
    while(running):
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = (process.communicate()[0]).encode('ascii','ignore')
        if((stdout.find(status) != -1)):
            running = False
        else:
            print "some dropbox process is still running"
            time.sleep(1)
    
def clean_directory(smashdir, fname):        
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+fname+"/Dropbox"))
    cmd = ('rm -rf '+(d+"/*"))
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
    
def start_dropbox(fname, smashdir, get_running=True):
    import os
    from os.path import expanduser
    from multiprocessing import Process
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/mdroboxinstances.sh "+expanduser("~")+" "+ d
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,)
    if(get_running==True):
        import time
        nbsr = NonBlockingStreamReader(process.stdout)
        while True:
            output = nbsr.readline(0.1)
            if output:
                print output
            stdout = check_status_dropbox(str(fname), smashdir)
            if((stdout.find("Up to date") != -1)):
                break
            elif((stdout.find("link") != -1)):
                print stdout
            time.sleep(1)
            
                
        cmd = os.path.dirname(__file__)+"/dropbox.py --set "+d+"/.dropbox lansync n"  
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        process.wait() 
        
def get_running_dropbox(fname, smashdir,status="Up to date"):
    import time
    up_to_date_flag=0
    timeout_flag=0
    stdout_array=[]
    while (up_to_date_flag < 2): 
        stdout = check_status_dropbox(fname, smashdir)
        stdout_array.append("%s - %s"%(time_now(),stdout))
        if((stdout.find(status) != -1)):
            up_to_date_flag += 1
        else:
            up_to_date_flag = 0
        time.sleep(0.01)
        
    return { fname : stdout_array } 

def dropbox_add_workers_to_conf(fname, smashdir):
    clean_directory(smashdir, fname) 
    
    if(check_status_dropbox(fname, smashdir).find("Up to date") == -1):
        start_dropbox(fname, smashdir)
    
    if(get_running_dropbox(str(fname), smashdir) != None):
        pass

def check_status_dropbox(fname, smashdir):
    import os
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/dropbox.py --set "+d+"/.dropbox status"    
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return (process.communicate()[0]).encode('ascii','ignore')

def prepare_smashbox(smashdir,worker_name_array,boss):
    if(get_running_dropbox(boss, smashdir) != None):
        stop_dropbox(boss, smashdir)#stop_dropbox(boss, smashdir)
        #print "BOSS DONE"
        
    for i in range(0, len(worker_name_array)):
        fname = worker_name_array[i]
        stop_dropbox(fname, smashdir)
    
    check_if_dropbox_stopped()  
    
def stop_dropbox(fname, smashdir):
    import os
    import time
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/dropbox.py --set "+d+"/.dropbox stop"  
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 

def dropbox_restart(smashdir, worker_name, local_folder):
    import time
    def dropbox_check_resume_sync(smashdir, worker_name):
        indexing_flag=True  
        while(indexing_flag):
            stdout = check_status_dropbox(worker_name, smashdir)
            #(stdout.find("Connecting") != -1) or 
            if((stdout.find("Indexing") != -1) or (stdout.find("Downloading") != -1) or (stdout.find("Up to date") != -1)):
                indexing_flag = False
        return time_now()
    #main
    start_dropbox(worker_name, smashdir, get_running=False)
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+worker_name))
    cmd = os.path.dirname(__file__)+"/dropbox.py --set "+d+"/.dropbox lansync n"  
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 
    cmd = os.path.dirname(__file__)+"/dropbox.py --set "+d+"/.dropbox exclude remove "+local_folder
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 
    indexing = dropbox_check_resume_sync(smashdir, worker_name)
    return indexing
      
""" seafile section """                   
class seafile:
    def __init__(self):
        pass
    
    @staticmethod   
    def sync_client_start(args,kwargs):
        import time
        smash_workers = args[0].workers
        smashdir = config.smashdir
        directory = install_seafile(smashdir,config.oc_webdav_endpoint)
        start_seafile("boss", smashdir,directory,config)
        seafile_clean_directory(smashdir, "boss")
        print "cleaned 1"
        start_seafile("boss", smashdir,directory,config)
        seafile_clean_directory(smashdir, "boss")
        print "cleaned 2"
        worker_name_array = []   
        for i,f_n in enumerate(smash_workers):
            f = f_n[0]
            fname = f_n[1]
            if fname is None:
                fname = f.__name__ 
            print fname,directory
            worker_name_array.append(fname) 
            start_seafile(fname, smashdir,directory,config) 
            seafile_clean_directory(smashdir, fname)
            print "cleaned 1"
            start_seafile(fname, smashdir,directory,config) 
            seafile_clean_directory(smashdir, fname)
            print "cleaned 2"
        
    @staticmethod
    def sync_client_finish(args,kwargs):
        pass
    
    @staticmethod
    def sync_client_step(args,kwargs):
        check_if_stopped("ccnet")
    
    @staticmethod
    def sync_client_stop(args,kwargs):
        pass    
    
    @staticmethod      
    def sync_engine(args,kwargs):
        worker_name = reflection.getProcessName()
        option = args[4]
        stop = True
        finish = False
        exclude = False
        smashdir = config.smashdir
        if option:
            for opt in option:
                if opt=='exclude_time':
                    exclude = True
                elif opt=='start_only':
                    stop = False
                elif opt=='finish_only':
                    finish = True
        if finish==False:
            run_seafile(smashdir, worker_name)
        get_running_seafile(worker_name, smashdir)
        t0 = datetime.datetime.now()
        log = get_synced_seafile(worker_name, smashdir)
        result = [t0,datetime.datetime.now()]
        sync_exec_time = result[1]-result[0]
        if stop==True:
            stop_seafile(worker_name, smashdir)
        if exclude==True:
            return None
        log_test(smashdir,log)
        return result,sync_exec_time
    
    @staticmethod   
    def oc_webdav_url(args,kwargs):
        return config.oc_server
    
    @staticmethod 
    def make_workdir(args,kwargs):
        name = None
        for key, value in kwargs.iteritems():
            if key=='name':
                name = value
        if name is None:
            name = reflection.getProcessName()
        workerdir = os.path.abspath(config.smashdir+"/seafile-"+name)
        return workerdir
    
    @staticmethod
    def hello():
        print "Hello world!"
        
    @staticmethod
    def stop(pid):
        print "Stopping..",pid
        kill_if_not_stopped("ccnet")
        reinit_seafile()
        stop_execution(pid)
        
""" seafile utilities """
def run_seafile(smashdir, fname):
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerdir = os.path.abspath(smashdir+"/seafile-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
    
def install_seafile(smashdir,version):
    from os.path import expanduser
    import platform
    def is_32bit():
        if (platform.architecture()[0]).find("64") != -1:
            return "seafile-cli_"+version+"_x86-64"
        else:
            return "seafile-cli_"+version+"_i386"
    home = expanduser("~")
    directory = home + "/seafile-cli-"+version
    if not os.path.exists(directory):
        print "%s does not exists, begin installation.."%directory
        dist = 'https://bintray.com/artifact/download/seafile-org/seafile/%s.tar.gz'%is_32bit()
        subprocess.call(["wget", "-O", "seafile-cli.tar.gz",dist], cwd=home)
        print "downloaded, unpack"
        subprocess.call(["tar", "-xvzf", "seafile-cli.tar.gz"], cwd=home)
        print "seafile installed"
    
    return directory
    
def start_seafile(fname, smashdir,directory,config):
    from os.path import expanduser
    home = expanduser("~")
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerdir = os.path.abspath(smashdir+"/seafile-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    
    protocol = "http"
    if config.oc_ssl_enabled:
        protocol += 's'
    oc_server = protocol + '://' + config.oc_server
    if not os.path.exists(parentdir):
        subprocess.call(["cp", "-R", directory, parentdir], cwd=home)
        subprocess.call(["mkdir", workerdir], cwd=home) 
        subprocess.call(["mkdir", os.path.abspath(smashdir+"/seafile-c-"+fname)], cwd=home) 
        subprocess.call(["./seaf-cli", "init", "-c",workerconfdir,"-d", parentdir], cwd=parentdir)
        subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
        while (not os.path.exists(os.path.join(parentdir,'seafile'))) or (not os.path.exists(os.path.join(parentdir,'seafile-data'))):
            subprocess.call(["./seaf-cli", "stop", "-c",workerconfdir], cwd=parentdir)
            subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
        subprocess.call(["./seaf-cli", "config", "-c",workerconfdir,"-k","disable_verify_certificate","-v","true"], cwd=parentdir)
        subprocess.call(["./seaf-cli", "stop", "-c",workerconfdir], cwd=parentdir)
        subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
        cmd_arr = ["./seaf-cli", "sync", "-c",workerconfdir, "-l",config.oc_server_folder,"-s",oc_server,"-u",config.oc_account_name,"-p",config.oc_account_password,"-d",workerdir]
        print cmd_arr
        subprocess.call(cmd_arr, cwd=parentdir)
    else:
        subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
    get_synced_seafile(fname, smashdir)
    stop_seafile(fname, smashdir)

def stop_seafile(fname, smashdir):
    import os
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    subprocess.call(["./seaf-cli", "stop", "-c",workerconfdir], cwd=parentdir)
    

def check_status_seafile(fname, smashdir):
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    cmd = "./seaf-cli status -c "+workerconfdir
    process = subprocess.Popen(cmd, cwd=parentdir, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return (process.communicate()[0]).encode('ascii','ignore')

def get_synced_seafile(fname, smashdir):
    import time
    flag = 0 
    stdout_array = []
    while flag<3:
        stdout = check_status_seafile(fname, smashdir)
        stdout_array.append("%s - %s"%(time_now(),stdout))
        if(stdout.find("synchronized") != -1):
            flag+=1
        else:
            flag=0
        time.sleep(0.05)
    return { fname : stdout_array }
    
def get_running_seafile(fname, smashdir):
    flag = 0
    while flag<2:
        if(((check_status_seafile(fname, smashdir)).find("waiting for sync") != -1)):
            flag+=1
    
def seafile_clean_directory(smashdir, fname): 
    workerdir = os.path.abspath(smashdir+"/seafile-"+fname)
    cmd = ('rm -rf '+os.path.join(workerdir,"*"))
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
    
def reinit_seafile():
    print "reinitialize seafile after corruption of fs"
    home = os.path.expanduser("~")
    subprocess.call("find %s -type d -name 'sea*' -exec rm -rf {} \;"%home, shell=True)
    
""" non native engines utilities """

def check_if_stopped(service):
    import time
    t_syncprepare = time_now() 
    running = True
    cmd = os.path.dirname(__file__)+"/running.sh "+service
    status = "Process not running"
    while(running):
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = (process.communicate()[0]).encode('ascii','ignore')
        if((stdout.find(status) != -1)):
            running = False
        else:
            print "some %s process is still running: %s"%(service,stdout)
            time.sleep(1)
            
def kill_if_not_stopped(service):
    import time
    running = True
    cmd = os.path.dirname(__file__)+"/python/smashbox/test_manager/running.sh "+service
    status = "Process not running"
    while(running):
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = (process.communicate()[0]).encode('ascii','ignore')
        if((stdout.find(status) != -1)):
            running = False
        else:
            print "some %s process is still running: %s"%(service,stdout)
            import re
            kill_array = re.findall(r'\d+', stdout)
            for pid in kill_array:
                stop_execution(int(pid))
            time.sleep(1)
            
def time_now(time_zero=None): 
    import datetime
    if time_zero==None:
        return datetime.datetime.now()
    else:
        return (datetime.datetime.now()-time_zero)  

def log_test(log_location,data):
    import io,json
    with io.open(log_location, 'a', encoding='utf-8') as file:
        file.write(unicode(json.dumps(data, ensure_ascii=False, indent=4)))  
  
from threading import Thread
from Queue import Queue, Empty

class NonBlockingStreamReader:

    def __init__(self, stream):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            while True:
                line = stream.readline()
                if line:
                    queue.put(line)
                else:
                    pass

        self._t = Thread(target = _populateQueue,
                args = (self._s, self._q))
        self._t.daemon = True
        self._t.start() #start collecting lines from the stream

    def readline(self, timeout = None):
        try:
            return self._q.get(block = timeout is not None,
                    timeout = timeout)
        except Empty:
            return None            