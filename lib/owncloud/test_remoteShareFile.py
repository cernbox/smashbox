
__doc__ = """

Test basic file remote-sharing between users.

+-----------+----------------------+------------------+----------------------------+
|  Step     |  Sharer              |  Sharee One      |  Sharee Two                |
|  Number   |                      |                  |                            |
+===========+======================+==================+============================|
|  2        | create work dir      | create work dir  |  create work dir           |
+-----------+----------------------+------------------+----------------------------+
|  3        | Create test files    |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  4        | Shares files with    |                  |                            |
|           | Sharee One           |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  5        |                      | Syncs and        |                            |
|           |                      | validates files  |                            |
+-----------+----------------------+------------------+----------------------------+
|  6        |                      | modifies one     |                            |
|           |                      | files, if        |                            |
|           |                      | permitted        |                            |
+-----------+----------------------+------------------+----------------------------+
|  7        | Validates modified   |                  |                            |
|           | file or not, based   |                  |                            |
|           | on permissions       |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  8        |                      | Shares a file    |                            |
|           |                      | with sharee two  |                            |
|           |                      | if permitted     |                            |
+-----------+----------------------+------------------+----------------------------+
|  9        |                      |                  |  Syncs and validates       |
|           |                      |                  |file is shared if permitted |
+-----------+----------------------+------------------+----------------------------+
|  10       | Sharer unshares a    |                  |                            |
|           | file                 |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  11       |                      | Syncs and        | Syncs and validates        |
|           |                      | validates file   | file not present           |
|           |                      | not present      |                            |
+-----------+----------------------+------------------+----------------------------+
|  12       | Sharer deletes a     |                  |                            |
|           | file                 |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  13       |                      | Syncs and        |                            |
|           |                      | validates file   |                            |
|           |                      | not present      |                            |
+-----------+----------------------+------------------+----------------------------+
| 14        | Final step           | Final step       |        Final Step          |
+-----------+----------------------+------------------+----------------------------+


Data Providers:

  test_sharePermissions:      Permissions to be applied to the share

"""

from smashbox.utilities import *
from smashbox.owncloudorg.remote_sharing import *

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

filesizeKB = int(config.get('share_filesizeKB', 10))
sharePermissions = int(config.get('test_sharePermissions', OCS_PERMISSION_ALL))

testsets = [
    {
        'test_sharePermissions': OCS_PERMISSION_ALL
    },
    {
        'test_sharePermissions': OCS_PERMISSION_READ | OCS_PERMISSION_UPDATE
    },
    {
        'test_sharePermissions': OCS_PERMISSION_READ | OCS_PERMISSION_SHARE
    }
]


@add_worker
def sharer(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(3, 'Create initial test files and directories')

    createfile(os.path.join(d, 'TEST_FILE_USER_SHARE.dat'), '0', count=1000, bs=filesizeKB)
    createfile(os.path.join(d, 'TEST_FILE_USER_RESHARE.dat'), '0', count=1000, bs=filesizeKB)
    createfile(os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat'), '0', count=1000, bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_sharer'] = md5sum(os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat'))
    logger.info('md5_sharer: %s', shared['md5_sharer'])

    list_files(d)
    run_ocsync(d, user_num=1)
    list_files(d)

    step(4, 'Sharer shares files')

    user1 = "%s%i" % (config.oc_account_name, 1)
    user2 = "%s%i" % (config.oc_account_name, 2)

    kwargs = {'perms': sharePermissions}
    shared['TEST_FILE_USER_SHARE'] = remote_share_file_with_user(
        'TEST_FILE_USER_SHARE.dat', user1, user2, **kwargs
    )
    shared['TEST_FILE_USER_RESHARE'] = remote_share_file_with_user(
        'TEST_FILE_USER_RESHARE.dat', user1, user2, **kwargs
    )
    shared['TEST_FILE_MODIFIED_USER_SHARE'] = remote_share_file_with_user(
        'TEST_FILE_MODIFIED_USER_SHARE.dat', user1, user2, **kwargs
    )
    shared['sharer.TEST_FILE_MODIFIED_USER_SHARE'] = os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat')

    step(7, 'Sharer validates modified file')
    run_ocsync(d, user_num=1)

    if not sharePermissions & OCS_PERMISSION_UPDATE:
        expect_not_modified(os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])
    else:
        expect_modified(os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])

    step(10, 'Sharer unshares a file')
    delete_share(user1, shared['TEST_FILE_USER_RESHARE'])

    step(12, 'Sharer deletes file')

    list_files(d)
    remove_file(os.path.join(d, 'TEST_FILE_USER_SHARE.dat'))
    run_ocsync(d, user_num=1)
    list_files(d)

    step(14, 'Sharer final step')


@add_worker
def sharee_one(step):

    step(2, 'Sharee One creates workdir')
    d = make_workdir()

    step(5, 'Sharee One syncs and validate files exist')

    run_ocsync(d, user_num=2)
    list_files(d)

    # Accept the remote shares for user2
    user2 = "%s%i" % (config.oc_account_name, 2)
    openShares = list_open_remote_share(user2)
    for share in openShares:
        accept_remote_share(user2, int(share['id']))
    sleep(5)

    run_ocsync(d, user_num=2)
    list_files(d)

    shared_file = os.path.join(d, 'TEST_FILE_USER_SHARE.dat')
    logger.info('Checking that %s is present in local directory for Sharee One', shared_file)
    expect_exists(shared_file)

    shared_file = os.path.join(d, 'TEST_FILE_USER_RESHARE.dat')
    logger.info('Checking that %s is present in local directory for Sharee One', shared_file)
    expect_exists(shared_file)

    shared_file = os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat')
    logger.info('Checking that %s is present in local directory for Sharee One', shared_file)
    expect_exists(shared_file)

    step(6, 'Sharee One modifies TEST_FILE_MODIFIED_USER_SHARE.dat')

    modify_file(os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat'), '1', count=10, bs=filesizeKB)
    run_ocsync(d, user_num=2)
    list_files(d)

    shared = reflection.getSharedObject()
    if not sharePermissions & OCS_PERMISSION_UPDATE:
        # local file is modified, but not synced so the owner still has the right file
        list_files(d)
        expect_modified(os.path.join(d, 'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])
        expect_not_modified(shared['sharer.TEST_FILE_MODIFIED_USER_SHARE'], shared['md5_sharer'])

    step(8, 'Sharee One share files with user 3')

    user2 = "%s%i" % (config.oc_account_name, 2)
    user3 = "%s%i" % (config.oc_account_name, 3)
    kwargs = {'perms': sharePermissions}
    result = remote_share_file_with_user('TEST_FILE_USER_RESHARE.dat', user2, user3, **kwargs)

    # FIXME Remote sharing ignores the share permission for now, so sharing should always work:
    # FIXME https://github.com/owncloud/core/issues/22495
    # if not sharePermissions & OCS_PERMISSION_SHARE:
    #     error_check(result != -1, "An error should have occurred while sharing the file, but it worked")
    # else:
    #     error_check(result != -1, "An error occurred while sharing the file")
    error_check(result != -1, "An error occurred while sharing the file")

    step(11, 'Sharee one validates file does not exist after unsharing')

    run_ocsync(d, user_num=2)
    list_files(d)

    shared_file = os.path.join(d, 'TEST_FILE_USER_RESHARE.dat')
    logger.info('Checking that %s is not present in sharee local directory', shared_file)
    expect_does_not_exist(shared_file)

    step(13, 'Sharee syncs and validates file does not exist')

    run_ocsync(d, user_num=2)
    list_files(d)

    # May seem weird, but that is the current behaviour. The file is still there locally,
    # but on the server the entry is a StorageNotAvailable exception, so webdav exists should not pass.
    shared_file = os.path.join(d, 'TEST_FILE_USER_SHARE.dat')
    logger.info('Checking that %s is present in sharee locally but not on webdav directory', shared_file)
    expect_exists(shared_file)
    expect_webdav_does_not_exist(shared_file, user_num=2)

    step(14, 'Sharee One final step')


@add_worker
def sharee_two(step):
  
    step(2, 'Sharee Two creates workdir')
    d = make_workdir()

    step(9, 'Sharee two validates share file')

    run_ocsync(d, user_num=3)
    list_files(d)

    # Accept the remote shares for user3
    user3 = "%s%i" % (config.oc_account_name, 3)
    openShares = list_open_remote_share(user3)
    for share in openShares:
        accept_remote_share(user3, int(share['id']))

    run_ocsync(d, user_num=3)
    list_files(d)

    shared_file = os.path.join(d, 'TEST_FILE_USER_RESHARE.dat')

    # FIXME Remote sharing ignores the share permission for now, so sharing should always work:
    # FIXME https://github.com/owncloud/core/issues/22495
    # if not sharePermissions & OCS_PERMISSION_SHARE:
    #     logger.info('Checking that %s is not present in local directory for Sharee Two', shared_file)
    #     expect_does_not_exist(shared_file)
    # else:
    #     logger.info('Checking that %s is present in local directory for Sharee Two', shared_file)
    #     expect_exists(shared_file)
    logger.info('Checking that %s is present in local directory for Sharee Two', shared_file)
    expect_exists(shared_file)

    step(11, 'Sharee two validates file does not exist after unsharing')

    run_ocsync(d, user_num=3)
    list_files(d)

    shared_file = os.path.join(d, 'TEST_FILE_USER_RESHARE.dat')

    # FIXME Remote sharing ignores the share permission for now, so sharing should always work:
    # FIXME https://github.com/owncloud/core/issues/22495
    # if not sharePermissions & OCS_PERMISSION_SHARE:
    #     logger.info('Checking that %s is not present in sharee locally or the webdav directory', shared_file)
    #     expect_does_not_exist(shared_file)
    #     expect_webdav_does_not_exist(shared_file, user_num=3)
    # else:
    #     # May seem weird, but that is the current behaviour. The file is still there locally,
    #     # but on the server the entry is a StorageNotAvailable exception, so webdav exists should not pass.
    #     logger.info('Checking that %s is present in sharee locally but not on webdav directory', shared_file)
    #     expect_exists(shared_file)
    #     expect_webdav_does_not_exist(shared_file, user_num=3)
    logger.info('Checking that %s is present in sharee locally but not on webdav directory', shared_file)
    expect_exists(shared_file)
    expect_webdav_does_not_exist(shared_file, user_num=3)

    step(14, 'Sharee Two final step')
