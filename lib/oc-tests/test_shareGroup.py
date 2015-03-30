
__doc__ = """

Test basic file sharing between users in a group.  

+-----------+-----------------+------------------+------------------+--------------+
|  Step     |  Sharer         |  Sharee One      |  Sharee Two      |  Admin       |
|  Number   |                 |  (not in group)  |  (in group)      |              |
+===========+======================+==================+============================|
|  2        | create work dir | create work dir  |  create work dir |              |
+-----------+-----------------+------------------+------------------+--------------+
|  3        | Create test     |                  |                  |              |
|           | files and dir   |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  4        | Shares files    |                  |                  |              |
|           | with group      |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  5        |                 | Syncs and        | Syncs and        |              |
|           |                 | validates files  | validates files  |              |
|           |                 | do not exist     | exist            |              |
+-----------+-----------------+------------------+------------------+--------------+
|  6        |                 |                  | Modifies one     |              |
|           |                 |                  | file, if allowed |              |
+-----------+-----------------+------------------+------------------+--------------+
|  7        | Validates       |                  |                  |              |
|           | file modified   |                  |                  |              |
|           | or not,         |                  |                  |              |
|           | based on        |                  |                  |              |
|           | permissions     |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  8        |                 |                  |  Shares a file   |              |
|           |                 |                  |  with sharee one |              |
|           |                 |                  |  if permitted    |              |
+-----------+-----------------+------------------+------------------+--------------+
|  9        |                 | Syncs and        |                  |              |
|           |                 | validates file   |                  |              |
|           |                 | is shared if     |                  |              |
|           |                 | permitted        |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  10       | Sharer unshares |                  |                  |              |
|           | a file          |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  11       |                 | Syncs and        | Syncs and        |              |
|           |                 | validates file   | validates file   |              |
|           |                 | not present      | not present      |              |
+-----------+-----------------+------------------+------------------+--------------+
|  12       | Sharer deletes  |                  |                  |              |
|           | a file          |                  |                  |              |
+-----------+-----------------+------------------+------------------+--------------+
|  13       |                 | Syncs and        |  Syncs and       |              |
|           |                 | validates file   |  validates file  |              |
|           |                 | not present      |  not present     |              |
+-----------+-----------------+------------------+------------------+--------------+
| 14        |                 |                  |                  | Removes user |
|           |                 |                  |                  | from Group   |
+-----------+-----------------+------------------+------------------+--------------+
| 15        |                 |                  |  Syncs and       |              |
|           |                 |                  |  verifies file   |              |
|           |                 |                  |  not present     |              |
+-----------+-----------------+------------------+------------------+--------------+
| 16        | Final step      | Final step       |  Final Step      | Final Step   |
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

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account(config.oc_number_test_users)
    check_users(num_test_users=config.oc_number_test_users)

    reset_owncloud_group(num_groups=config.oc_number_test_groups)
    check_groups(config.oc_number_test_groups)

    add_user_to_group('user3', 'testgroup1')

    reset_rundir()
    reset_server_log_file()

    step (17, 'Validate server log file is clean')

    d = make_workdir()
    scrape_log_file(d)


@add_worker
def sharer(step):

    step (2, 'Create workdir')
    d = make_workdir()

    step (3, 'Create initial test files and directories')

    createfile(os.path.join(d,'TEST_FILE_GROUP_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_GROUP_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_sharer'] = md5sum(os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat'))
    logger.info('md5_sharer: %s',shared['md5_sharer'])

    list_files(d)
    run_ocsync(d,user_num=1)
    list_files(d)

    step (4, 'Sharer shares files')

    user1 = "%s%i"%(config.oc_account_name, 1)
    group = "%s%i"%(config.oc_group_name, 1)

    kwargs = {'perms': OCS_PERMISSION_ALL}
    shared['TEST_FILE_GROUP_SHARE'] = share_file_with_group ('TEST_FILE_GROUP_SHARE.dat', user1, group, **kwargs)
    shared['TEST_FILE_GROUP_RESHARE'] = share_file_with_group ('TEST_FILE_GROUP_RESHARE.dat', user1, group, **kwargs)
    shared['TEST_FILE_MODIFIED_GROUP_SHARE'] = share_file_with_group ('TEST_FILE_MODIFIED_GROUP_SHARE.dat', user1, group, **kwargs)

    step (7, 'Sharer validates modified file')
    run_ocsync(d,user_num=1)
    expect_modified(os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat'), shared['md5_sharer'])

    step (10, 'Sharer unshares a file')
    delete_share (user1, shared['TEST_FILE_GROUP_RESHARE'])

    step (12, 'Sharer deletes file')

    list_files(d)
    remove_file(os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat'))
    run_ocsync(d,user_num=1)
    list_files(d)

    step (16, 'Sharer Final step')

@add_worker
def shareeOne(step):

    step (2, 'Sharee One creates workdir')
    d = make_workdir()

    step (5, 'Sharee One syncs and validate files do not exist')

    run_ocsync(d,user_num=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_SHARE.dat')
    logger.info ('Checking that %s is not present in local directory for Sharee One', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_RESHARE.dat')
    logger.info ('Checking that %s is not present in local directory for Sharee One', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat')
    logger.info ('Checking that %s is not present in local directory for Sharee One', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (9, 'Sharee one validates share file')

    run_ocsync(d,user_num=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (11, 'Sharee one validates file does not exist after unsharing')

    run_ocsync(d,user_num=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_RESHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (13, 'Sharee One syncs and validates file does not exist')

    run_ocsync(d,user_num=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_SHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (16, 'Sharee One final step')

@add_worker
def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    step (5, 'Sharee Two syncs and validate files do exist')

    run_ocsync(d,user_num=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_SHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (6, 'Sharee Two modifies TEST_FILE_MODIFIED_GROUP_SHARE.dat')

    modify_file(os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat'),'1',count=10,bs=filesizeKB)
    run_ocsync(d,user_num=3)
    list_files(d)

    step (8, 'Sharee Two shares file with Sharee One')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': OCS_PERMISSION_ALL}
    share_file_with_user ('TEST_FILE_GROUP_RESHARE.dat', user3, user2, **kwargs)

    step (11, 'Sharee two validates file does not exist after unsharing')

    run_ocsync(d,user_num=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_RESHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)
    step (13, 'Sharee two validates file does not exist after deleting')

    run_ocsync(d,user_num=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_MODIFIED_GROUP_SHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)
    step (15, 'Sharee two validates file does not exist after being removed from group')

    run_ocsync(d,user_num=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_GROUP_SHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (16, 'Sharee Two final step')

@add_worker
def admin(step):


    step (14, 'Admin user removes user from group')
    remove_user_from_group('user3', 'testgroup1')

    step (16, 'Admin final step')

