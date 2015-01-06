
__doc__ = """ Test basic sharing between two users """

from smashbox.utilities import *
import glob

filesizeKB = int(config.get('share_filesizeKB',10))

def expect_modified (fn, md5):

    actual_md5 = md5sum(fn)
    error_check(actual_md5 != md5, "md5 of modified file %s did not change: expected %s, got %s"%(fn,md5,actual_md5))

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account()
    check_users()

    reset_owncloud_group()
    check_groups()

    addUserToGroup('user3', 'testgroup1')

    reset_rundir()

@add_worker
def sharer(step):

    step (2,'Create workdir')
    d = make_workdir()

    step (3,'Create initial test files and directories')

    createfile(os.path.join(d,'TEST_FILE_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_USER_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    createfile(os.path.join(d,'TEST_FILE_GROUP_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_GROUP_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    testDir = make_workdir('test_sync_dir')

    createfile(os.path.join(testDir,'TEST_DIR_FILE_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(testDir,'TEST_DIR_FILE_USER_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(testDir,'TEST_DIR_FILE_MODIFIED_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(testDir,'TEST_DIR_FILE_GROUP_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(testDir,'TEST_DIR_FILE_GROUP_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(testDir,'TEST_DIR_FILE_MODIFIED_GROUP_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_sharer'] = md5sum(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'))
    logger.info('md5_sharer: %s',shared['md5_sharer'])

    list_files(d)
    run_ocsync(d)
    list_files(d)

    step(4,'Sharer shares files')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)
    shareFileWithUser ('TEST_FILE_USER_SHARE.dat', user1, user2)
    shareFileWithUser ('TEST_FILE_USER_RESHARE.dat', user1, user2)
    shareFileWithUser ('TEST_FILE_MODIFIED_USER_SHARE.dat', user1, user2)

    step(7, 'Sharer validates modified file')
    run_ocsync(d)
    expect_modified(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])

    step(8,'Sharer deletes file')

    list_files(d)
    removeFile(os.path.join(d,'TEST_FILE_USER_SHARE.dat'))
    run_ocsync(d)
    list_files(d)

    step(10, 'Sharer creates new file and shares with group')

    createfile(os.path.join(d,'TEST_FILE_GROUP_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_creator'] = md5sum(os.path.join(d,'TEST_FILE_GROUP_SHARE.dat'))
    logger.info('md5_creator: %s',shared['md5_creator'])

    list_files(d)
    run_ocsync(d)
    list_files(d)

    group = "%s%i"%(config.oc_group_name, 1)
    shareFileWithGroup ('TEST_FILE_GROUP_SHARE.dat', user1, group)

    step (13, 'Sharer Final step')

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

    step(9,'Sharee syncs and validates file does not exist')

    run_ocsync(d,userNum=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_SHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step(11,'Group sharee syncs and validates file exists')

    run_ocsync(d,userNum=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_SHARE.dat')
    logger.info ('Checking that %s is present in sharee local directory', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (12,'Group sharee one is removed from group, syncs, and validates file does not exists')

    removeUserFromGroup('user3', 'testgroup1')

    run_ocsync(d,userNum=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_SHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (13, 'Sharee One final step')

@add_worker
def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    step (11, 'Sharee Two final step')

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

