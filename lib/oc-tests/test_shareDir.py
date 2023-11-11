
__doc__ = """

Test basic directory and file sharing between users.  

+-----------+-----------------+------------------+------------------+--------------+
|  Step     |  Sharer         |  Sharee One      |  Sharee Two      |  Admin       |
|  Number   |                 |  (not in group)  |  (in group)      |              |
+===========+======================+==================+============================|
|  2        | create work dir | create work dir  |  create work dir |              |
+-----------+-----------------+------------------+------------------+--------------+
|  3        | Create test     |                  |                  |              |
|           | files and dir   |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  4        | Share directory |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  5        |                 | Syncs and        |                  |              |
|           |                 | validates        |                  |              |
|           |                 | directory exists |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  6        |                 | Modifies one     |                  |              |
|           |                 | file, if allowed |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  7        | Validates       |                  |                  |              |
|           | file modified   |                  |                  |              |
|           | or not,         |                  |                  |              |
|           | based on        |                  |                  |              |
|           | permissions     |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  8        |                 | Creates a new    |                  |              |
|           |                 | file in the      |                  |              |
|           |                 | directory        |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  9        | Validates new   |                  |                  |              |
|           | file exists     |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  10       |                 | Deletes a file   |                  |              |
|           |                 | from the         |                  |              |
|           |                 | directory        |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  11       | Validates file  |                  |                  |              |
|           | does not exist  |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  12       |                 |  Shares a file   |                  |              |
|           |                 |  with Sharee two |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  13       |                 |                  |  Syncs and       |              |
|           |                 |                  |  validates file  |              |
|           |                 |                  |  present         |              |
+-----------+-----------------+------------------+------------------+--------------+
|  14       |                 | Re-shares the    |                  |              |
|           |                 | directory with   |                  |              |
|           |                 | Sharee Two       |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  15       |                 |                  |  Syncs and       |              |
|           |                 |                  |  verifies        |              |
|           |                 |                  |  directory       |              |
+-----------+-----------------+------------------+------------------+--------------+
|  16       | Unshares the    |                  |                  |              |
|           | directory       |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  17       |                 | Syncs and        |                  |              |
|           |                 | validates        |                  |              |
|           |                 | directory gone   |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  18       |                 |                  | Syncs and        |              |
|           |                 |                  | validates        |              |
|           |                 |                  | directory is     |              |
|           |                 |                  | gone (<9.0) or   |              |
|           |                 |                  | still there      |              |
|           |                 |                  | (9.0+)           |              |
+-----------+-----------------+------------------+------------------+--------------+
|  19       | Final step      | Final step       |  Final Step      |              |
+-----------+-----------------+------------------+------------------+--------------+


Data Providers:

"""

from smashbox.utilities import *
import glob

filesizeKB = int(config.get('share_filesizeKB',10))

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

# True => use new webdav endpoint (dav/files)
# False => use old webdav endpoint (webdav)
use_new_dav_endpoint = bool(config.get('use_new_dav_endpoint',True))

testsets = [
        {
          'use_new_dav_endpoint':False
        },
        {
          'use_new_dav_endpoint':True
        }
]

def finish_if_not_capable():
    # Finish the test if some of the prerequisites for this test are not satisfied
    if compare_oc_version('10.0', '<') and use_new_dav_endpoint == True:
        #Dont test for <= 9.1 with new endpoint, since it is not supported
        logger.warn("Skipping test since webdav endpoint is not capable for this server version")
        return True
    return False

@add_worker
def setup(step):
    if finish_if_not_capable():
        return

    step (1, 'create test users')
    reset_owncloud_account(num_test_users=config.oc_number_test_users)
    check_users(config.oc_number_test_users)

    reset_rundir()

@add_worker
def sharer(step):
    if finish_if_not_capable():
        return

    step (2, 'Create workdir')
    d = make_workdir()

    step (3, 'Create initial test files and directories')

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
    run_ocsync(d,user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    step (4, 'Sharer shares directory')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)

    kwargs = {'perms': OCS_PERMISSION_ALL}

    shared['SHARE_LOCAL_DIR'] = share_file_with_user ('localShareDir', user1, user2, **kwargs)

    step (7, 'Sharer validates modified file')
    run_ocsync(d,user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)
    expect_modified(os.path.join(localDir,'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])

    step (9, 'Sharer validates newly added file')
    run_ocsync(d,user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)
    expect_exists(os.path.join(localDir,'TEST_FILE_NEW_USER_SHARE.dat'))

    step (11, 'Sharer validates deleted file')
    run_ocsync(d,user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)
    expect_does_not_exist(os.path.join(localDir,'TEST_FILE_NEW_USER_SHARE.dat'))

    step (16, 'Sharer unshares the directory')
    delete_share (user1, shared['SHARE_LOCAL_DIR'])

    step (19, 'Sharer Final step')

@add_worker
def shareeOne(step):
    if finish_if_not_capable():
        return

    step (2, 'Sharee One creates workdir')
    d = make_workdir()

    step (5, 'Sharee One syncs and validates directory exist')

    run_ocsync(d,user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    sharedDir = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedDir)
    error_check(os.path.exists(sharedDir), "Directory %s should exist" %sharedDir)

    step (6, 'Sharee One modifies TEST_FILE_MODIFIED_USER_SHARE.dat')

    modify_file(os.path.join(d,'localShareDir/TEST_FILE_MODIFIED_USER_SHARE.dat'),'1',count=10,bs=filesizeKB)
    run_ocsync(d,user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    step (8, 'Sharee One adds a file to the directory')
    createfile(os.path.join(d,'localShareDir/TEST_FILE_NEW_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    run_ocsync(d,user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    step (10, 'Sharee One deletes a file from the directory')
    fileToDelete = os.path.join(d,'localShareDir/TEST_FILE_NEW_USER_SHARE.dat')
    delete_file (fileToDelete)
    run_ocsync(d,user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    step (12, 'Sharee One share files with user 3')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': OCS_PERMISSION_ALL}
    share_file_with_user ('localShareDir/TEST_FILE_USER_RESHARE.dat', user2, user3, **kwargs)

    step (14, 'Sharee One share directory user 3')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': OCS_PERMISSION_ALL}
    share_file_with_user ('localShareDir', user2, user3, **kwargs)

    step (17, 'Sharee One syncs and validates directory does not exist')

    run_ocsync(d,user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    sharedFile = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    expect_does_not_exist(sharedFile)

    step (19, 'Sharee One final step')

@add_worker
def shareeTwo(step):
    if finish_if_not_capable():
        return
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    # create a folder so we get a naming conflict later when the folder is shared
    dirName = os.path.join(d,'localShareDir')
    make_workdir(dirName)

    # Do we want to test the client's conflict resolution or the server's?
    # Currently we test the server, to test the client comment out the sync below
    run_ocsync(d,user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    step (13, 'Sharee two validates share file')

    run_ocsync(d,user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    expect_exists(sharedFile)

    step (15, 'Sharee two validates directory re-share')

    run_ocsync(d,user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    localDir = os.path.join(d,'localShareDir')
    logger.info ('Checking that local dir %s is still present in local directory for Sharee Two', localDir)
    expect_exists(localDir)

    localDirFile = os.path.join(d,'localShareDir/TEST_FILE_USER_SHARE.dat')
    logger.info ('Checking that local dir does not contain the shared file %s for Sharee Two', localDirFile)
    expect_does_not_exist(localDirFile)

    sharedDir = os.path.join(d, 'localShareDir (2)')
    logger.info ('Checking that shared dir %s is present in local directory for Sharee Two', sharedDir)
    expect_exists(sharedDir)

    sharedDirFile = os.path.join(d, 'localShareDir (2)/TEST_FILE_USER_SHARE.dat')
    logger.info ('Checking that shared dir does contain the shared file %s for Sharee Two', sharedDirFile)
    expect_exists(sharedDirFile)

    if compare_oc_version('9.0', '<'):
        step(18, 'Sharee two syncs and validates directory does not exist')
    else:
        step(18, 'Sharee two syncs and validates directory does still exist')

    run_ocsync(d,user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    localDir = os.path.join(d, 'localShareDir')
    logger.info ('Checking that local directory %s is still present in sharee local directory', localDir)
    expect_exists(localDir)

    sharedDir = os.path.join(d, 'localShareDir (2)')
    if compare_oc_version('9.0', '<'):
        logger.info('Checking that %s is not present in sharee local directory', sharedDir)
        expect_does_not_exist(sharedDir)
    else:
        logger.info('Checking that %s is still present in sharee local directory', sharedDir)
        expect_exists(sharedDir)

    step (19, 'Sharee Two final step')
