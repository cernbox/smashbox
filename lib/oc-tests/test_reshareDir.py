
__doc__ = """

Test basic directory re-sharing between users.  This test is a sub-test of
test_shareDir.py

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
|  6        |                 |  Shares a file   |                  |              |
|           |                 |  with Sharee two |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  7        |                 |                  |  Syncs and       |              |
|           |                 |                  |  validates file  |              |
|           |                 |                  |  present         |              |
+-----------+-----------------+------------------+------------------+--------------+
|  8        | Final step      | Final step       |  Final Step      |              |
+-----------+-----------------+------------------+------------------+--------------+


Data Providers:

"""

from smashbox.utilities import *
import glob

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

filesizeKB = int(config.get('share_filesizeKB',10))

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account(num_test_users=config.oc_number_test_users)
    check_users(config.oc_number_test_users)

    reset_rundir()
    reset_server_log_file()

    step (9, 'Validate server log file is clean')

    d = make_workdir()
    scrape_log_file(d)


@add_worker
def sharer(step):

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
    run_ocsync(d,user_num=1)
    list_files(d)

    step (4, 'Sharer shares directory')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)

    kwargs = {'perms': OCS_PERMISSION_ALL}
    shared['SHARE_LOCAL_DIR'] = share_file_with_user ('localShareDir', user1, user2, **kwargs)

    step (8, 'Sharer Final step')

@add_worker
def shareeOne(step):

    step (2, 'Sharee One creates workdir')
    d = make_workdir()

    step (5, 'Sharee One syncs and validates directory exist')

    run_ocsync(d,user_num=2)
    list_files(d)

    sharedDir = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedDir)
    error_check(os.path.exists(sharedDir), "Directory %s should exist" %sharedDir)

    step (6, 'Sharee One share files with user 3')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': OCS_PERMISSION_ALL}
    share_file_with_user ('localShareDir/TEST_FILE_USER_RESHARE.dat', user2, user3, **kwargs)

    step (8, 'Sharee One final step')

@add_worker
def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    procName = reflection.getProcessName()
    dirName = "%s/%s"%(procName, 'localShareDir')
    localDir = make_workdir(dirName)

    step (13, 'Sharee two validates share file')

    run_ocsync(d,user_num=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (8, 'Sharee Two final step')


