
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

def expect_exists (fn):

    error_check(os.path.exists(fn), "File %s does not exist but should"%(fn))

def expect_does_not_exist (fn):

    error_check(not os.path.exists(fn), "File %s exists but should not"%(fn))

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

    procName = reflection.getProcessName()
    dirName = "%s/%s"%(procName, 'localShareDir')
    localDir = make_workdir(dirName)

    createfile(os.path.join(localDir,'TEST_FILE_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(localDir,'TEST_FILE_USER_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(localDir,'TEST_FILE_MODIFIED_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_sharer'] = md5sum(os.path.join(localDir,'TEST_FILE_MODIFIED_USER_SHARE.dat'))
    logger.info('md5_sharer: %s',shared['md5_sharer'])

    list_files(d)
    run_ocsync(d)
    list_files(d)

    step(4,'Sharer shares directory')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)

    kwargs = {'perms': OCS_PERMISSION_ALL}

    shared['SHARE_LOCAL_DIR'] = shareFileWithUser ('localShareDir', user1, user2, **kwargs)

    step(7, 'Sharer validates modified file')
    run_ocsync(d)
    expect_modified(os.path.join(localDir,'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])

    step (9, 'Sharer validates newly added file')
    run_ocsync(d)
    expect_exists(os.path.join(localDir,'TEST_FILE_NEW_USER_SHARE.dat'))

    step (11, 'Sharer validates deleted file')
    run_ocsync(d)
    expect_does_not_exist(os.path.join(localDir,'TEST_FILE_NEW_USER_SHARE.dat'))

    step (16, 'Sharer unshares the directory')
    deleteShare (user1, shared['SHARE_LOCAL_DIR'])

    step (19, 'Sharer Final step')

@add_worker
def shareeOne(step):

    step (2, 'Sharee One creates workdir')
    d = make_workdir()

    step(5,'Sharee One syncs and validates directory exist')

    run_ocsync(d,userNum=2)
    list_files(d)

    sharedDir = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedDir)
    error_check(os.path.exists(sharedDir), "Directory %s should exist" %sharedDir)

    step (6, 'Sharee One modifies TEST_FILE_MODIFIED_USER_SHARE.dat')

    modifyFile(os.path.join(d,'localShareDir/TEST_FILE_MODIFIED_USER_SHARE.dat'),'1',count=10,bs=filesizeKB)
    run_ocsync(d,userNum=2)
    list_files(d)

    step (8, 'Sharee One adds a file to the directory')
    createfile(os.path.join(d,'localShareDir/TEST_FILE_NEW_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    run_ocsync(d,userNum=2)
    list_files(d)

    step (10, 'Sharee One deletes a file from the directory')
    fileToDelete = os.path.join(d,'localShareDir/TEST_FILE_NEW_USER_SHARE.dat')
    deleteFile (fileToDelete)
    run_ocsync(d,userNum=2)
    list_files(d)

    step (12, 'Sharee One share files with user 3')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': OCS_PERMISSION_ALL}
    shareFileWithUser ('localShareDir/TEST_FILE_USER_RESHARE.dat', user2, user3, **kwargs)

    step (14, 'Sharee One share directory user 3')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': OCS_PERMISSION_ALL}
    shareFileWithUser ('localShareDir', user2, user3, **kwargs)

    step(17,'Sharee One syncs and validates directory does not exist')

    run_ocsync(d,userNum=2)
    list_files(d)

    sharedFile = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    expect_does_not_exist(sharedFile)

    step (19, 'Sharee One final step')

@add_worker
def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    procName = reflection.getProcessName()
    dirName = "%s/%s"%(procName, 'localShareDir')
    localDir = make_workdir(dirName)

    step (13, 'Sharee two validates share file')

    run_ocsync(d,userNum=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (15, 'Sharee two validates directory re-share')

    run_ocsync(d,userNum=3)
    list_files(d)

    sharedFile = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step(18,'Sharee One syncs and validates directory does not exist')

    run_ocsync(d,userNum=3)
    list_files(d)

    sharedFile = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    expect_does_not_exist(sharedFile)

    step (19, 'Sharee Two final step')

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

