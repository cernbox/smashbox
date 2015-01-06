
__doc__ = """ Test basic sharing between two users """

from smashbox.utilities import *
import glob

filesizeKB = int(config.get('share_filesizeKB',10))

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

def expect_modified (fn, md5):

    actual_md5 = md5sum(fn)
    error_check(actual_md5 != md5, "md5 of modified file %s did not change: expected %s, got %s"%(fn,md5,actual_md5))

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account()
    check_users()

    reset_rundir()

@add_worker
def sharer(step):

    step (2,'Create workdir')
    d = make_workdir()

    step (3,'Create initial test files and directories')

    createfile(os.path.join(d,'TEST_FILE_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_USER_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_sharer'] = md5sum(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'))
    logger.info('md5_sharer: %s',shared['md5_sharer'])

    list_files(d)
    run_ocsync(d)
    list_files(d)

    step(4,'Sharer shares files')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)

    kwargs = {'perms': OCS_PERMISSION_ALL}
    shared['TEST_FILE_USER_SHARE'] = shareFileWithUser ('TEST_FILE_USER_SHARE.dat', user1, user2, **kwargs)
    shared['TEST_FILE_USER_RESHARE'] = shareFileWithUser ('TEST_FILE_USER_RESHARE.dat', user1, user2, **kwargs)
    shared['TEST_FILE_MODIFIED_USER_SHARE'] = shareFileWithUser ('TEST_FILE_MODIFIED_USER_SHARE.dat', user1, user2, **kwargs)

    step(7, 'Sharer validates modified file')
    run_ocsync(d)
    expect_modified(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])

    step (10, 'Sharer unshares a file')
    deleteShare (user1, shared['TEST_FILE_USER_RESHARE'])

    step(12,'Sharer deletes file')

    list_files(d)
    removeFile(os.path.join(d,'TEST_FILE_USER_SHARE.dat'))
    run_ocsync(d)
    list_files(d)

# continue numbering here

    step (14, 'Sharer Final step')

@add_worker
def shareeOne(step):

    step (2, 'Sharee One creates workdir')
    d = make_workdir()

    step(5,'Sharee One syncs and validate files exist')

    run_ocsync(d,userNum=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_SHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (6, 'Sharee One modifies TEST_FILE_MODIFIED_USER_SHARE.dat')

    modifyFile(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'),'1',count=10,bs=filesizeKB)
    run_ocsync(d,userNum=2)
    list_files(d)

    step (8, 'Sharee One share files with user 3')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': OCS_PERMISSION_ALL}
    shareFileWithUser ('TEST_FILE_USER_RESHARE.dat', user2, user3, **kwargs)

    step (11, 'Sharee one validates file does not exist after unsharing')

    run_ocsync(d,userNum=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step(13,'Sharee syncs and validates file does not exist')

    run_ocsync(d,userNum=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_SHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

# continue numbering here

    step (14, 'Sharee One final step')

@add_worker
def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    step (9, 'Sharee two validates share file')

    run_ocsync(d,userNum=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (11, 'Sharee two validates file does not exist after unsharing')

    run_ocsync(d,userNum=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

# continue numbering here

    step (14, 'Sharee Two final step')

def check_users(numTestUsers=None):

   if numTestUsers is None:
     numTestUsers = config.oc_number_test_users

   for i in range(1, numTestUsers+1):
       username = "%s%i"%(config.oc_account_name, i)
       result = check_owncloud_account(username)
       error_check(int(result or 0) == 0, 'User %s not found'%username)

def check_groups(numGroups=1):

   for i in range(1, numGroups+1):
       groupname = "%s%i"%(config.oc_group_name, i)
       result = check_owncloud_group(groupname)
       error_check(int(result or 0) == 0, 'Group %s not found'%groupname)

