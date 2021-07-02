__doc__ = """

This test is oriented to test share mount initialization in most sharing cases. It checks for correct files propagation in
scenarios where user is receiving shared/reshared files and folders via group/user shares.

+-------+-----------------+----------------+-------------------+--------------+-----------------+
| step  | owner           | ownerRecipient | R2                | R3           | R4              |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 2     | create dir      |                | create dir        | create dir   | create dir      |
|       | share /test1    |                |                   |              |                 |
|       | -> R2 R3 (group)|                |                   |              |                 |
|       |                 |                |                   |              |                 |
|       | share /test2    |                |                   |              |                 |
|       | -> R4 (group)   |                |                   |              |                 |
|       |                 |                |                   |              |                 |
|       | share test1.txt |                |                   |              |                 |
|       | -> R3 (user)    |                |                   |              |                 |
|       |                 |                |                   |              |                 |
|       | share test2.txt |                |                   |              |                 |
|       | -> R4 (user)    |                |                   |              |                 |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 3     |                 |                | reshare directory | reshare file |                 |
|       |                 |                | -> R4             | -> R4        |                 |
|       |                 |                | /test1/sub        | test1.txt    |                 |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 4     | sync&check      | sync&check     | sync&check        | sync&check   | do noting yet   |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 5     | upload to       |                | upload to         | change       |                 |
|       | -> /test1       |                | -> /test1/sub     | -> test1.txt |                 |
|       | -> /test2       |                |                   |              |                 |
|       |                 |                |                   |              |                 |
|       | change          |                |                   |              |                 |
|       | -> test2.txt    |                |                   |              |                 |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 6     | sync&check      | sync&check     | sync&check        | sync&check   |                 |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 7     |                 |                |                   |              | sync&check      |
|       |                 |                |                   |              | (initMounts)    |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 8     |                 |                |                   |              | create dir      |
|       |                 |                |                   |              | -> shared       |
|       |                 |                |                   |              | -> reshared     |
|       |                 |                |                   |              |                 |
|       |                 |                |                   |              | move shared     |
|       |                 |                |                   |              | -> shared       |
|       |                 |                |                   |              |                 |
|       |                 |                |                   |              | move reshared   |
|       |                 |                |                   |              | -> reshared     |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 9     | sync&check      | sync&check     | sync&check        | sync&check   |                 |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
| 10    |                 |                |                   |              | resync&check    |
+-------+-----------------+----------------+-------------------+--------------+-----------------+
"""
from smashbox.utilities import *
import itertools
import os.path
import re
import operator as op

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

def get_group_name(i):
    return '%s%i' % (config.oc_group_name, i)

def get_account_name(i):
    return '%s%i' % (config.oc_account_name, i)

group_map = {
    # maps the group name with the usernum belonging to the group
    get_group_name(1) : [2,3],
    get_group_name(2) : [4,5],
    get_group_name(3) : [6,7],
    get_group_name(4) : [8,9],
}

def run_group_ocsync(d, group_name):
    for usernum in group_map[group_name]:
        run_ocsync(os.path.join(d, str(usernum)), user_num=usernum, use_new_dav_endpoint=use_new_dav_endpoint)

@add_worker
def setup(step):

    step(1, 'create test users')
    num_users = 9

    # Create additional accounts
    if config.oc_number_test_users < num_users:
            for i in range(config.oc_number_test_users + 1, num_users + 1):
                username = "%s%i" % (config.oc_account_name, i)
                delete_owncloud_account(username)
                create_owncloud_account(username, config.oc_account_password)
                login_owncloud_account(username, config.oc_account_password)

    check_users(num_users)
    reset_owncloud_group(num_groups=4)

    for group in group_map:
        for user in group_map[group]:
            add_user_to_group(get_account_name(user), group)

def finish_if_not_capable():
    # Finish the test if some of the prerequisites for this test are not satisfied
    if compare_oc_version('10.0', '<') and use_new_dav_endpoint == True:
        #Dont test for <= 9.1 with new endpoint, since it is not supported
        logger.warn("Skipping test since webdav endpoint is not capable for this server version")
        return True
    return False

@add_worker
def owner(step):
    if finish_if_not_capable():
        return

    user = '%s%i' % (config.oc_account_name, 1)

    step (2, 'Create workdir')
    d = make_workdir()

    mkdir(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    mkdir(os.path.join(d, 'TEST_SHARE_FOLDER'))

    shared = reflection.getSharedObject()
    createfile(os.path.join(d, 'TEST_RESHARE_FILE.dat'), '00', count=100, bs=10)
    shared['TEST_RESHARE_FILE'] = md5sum(os.path.join(d, 'TEST_RESHARE_FILE.dat'))

    createfile(os.path.join(d, 'TEST_SHARE_FILE.dat'), '01', count=100, bs=10)
    shared['TEST_SHARE_FILE'] = md5sum(os.path.join(d, 'TEST_SHARE_FILE.dat'))
    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
    client.login(user, config.oc_account_password)

    # Share with Group users R2 and R3
    group1 = get_group_name(1)
    share1_data = client.share_file_with_group('/TEST_RESHARE_SUBFOLDER', group1, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (group1,))

    user3 = '%s%i' % (config.oc_account_name, 3)
    share1_data = client.share_file_with_user('/TEST_RESHARE_FILE.dat', user3, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (group1,))

    # Share with Group user R4
    group2 = get_group_name(2)
    share2_data = client.share_file_with_group('/TEST_SHARE_FOLDER', group2, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (group2,))

    user4 = '%s%i' % (config.oc_account_name, 4)
    share2_data = client.share_file_with_user('/TEST_SHARE_FILE.dat', user4, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (group2,))

    step(5, 'Upload files to TEST_SHARE_FOLDER, TEST_RESHARE_SUBFOLDER and change TEST_SHARE_FILE')

    createfile(os.path.join(d, 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'), '02', count=100, bs=10)
    shared['TEST_SHARE_FOLDER_FILE'] = md5sum(os.path.join(d, 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'))

    createfile(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'), '03', count=100, bs=10)
    shared['TEST_RESHARE_SUBFOLDER_FILE'] = md5sum(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'))

    modify_file(os.path.join(d,'TEST_SHARE_FILE.dat'),'11',count=100,bs=10)
    shared['TEST_SHARE_FILE'] = md5sum(os.path.join(d, 'TEST_SHARE_FILE.dat'))

    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    step(6, 'Resync and check')

    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_exists(os.path.join(d, 'TEST_SHARE_FOLDER'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_SHARE_FILE.dat'), shared['TEST_SHARE_FILE'])

    expect_not_modified(os.path.join(d, 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'), shared['TEST_SHARE_FOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'), shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'), shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])

    step(8, 'Resync and check')

    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_exists(os.path.join(d, 'TEST_SHARE_FOLDER'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_SHARE_FILE.dat'), shared['TEST_SHARE_FILE'])

    expect_not_modified(os.path.join(d, 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'), shared['TEST_SHARE_FOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'), shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'), shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])

@add_worker
def ownerRecipient(step):
    if finish_if_not_capable():
        return

    step (2, 'Create workdir')
    d = make_workdir()

    step (4, 'Sync and check required files')

    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folder has been synced down
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))

    # Check that file has been synced down
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_SHARE_FILE.dat'), shared['TEST_SHARE_FILE'])

    step(6, 'Resync and check')

    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_exists(os.path.join(d, 'TEST_SHARE_FOLDER'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_SHARE_FILE.dat'), shared['TEST_SHARE_FILE'])

    expect_not_modified(os.path.join(d, 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'),
                        shared['TEST_SHARE_FOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])

    step(8, 'Resync and check')

    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_exists(os.path.join(d, 'TEST_SHARE_FOLDER'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_SHARE_FILE.dat'), shared['TEST_SHARE_FILE'])

    expect_not_modified(os.path.join(d, 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'),
                        shared['TEST_SHARE_FOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])

@add_worker
def recipient2(step):
    if finish_if_not_capable():
        return

    user = '%s%i' % (config.oc_account_name, 2)

    step (2, 'Create workdir')
    d = make_workdir()

    group2 = get_group_name(2)
    step(3, 'Reshare /TEST_RESHARE_SUBFOLDER/SUB with %s' % (group2))

    client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
    client.login(user, config.oc_account_password)
    # only the first user of the group shares with another group, to keep it simple
    share1_data = client.share_file_with_group('/TEST_RESHARE_SUBFOLDER/SUB', group2, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (group2))

    step(4, 'Sync and check required files')

    run_ocsync(d, user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that shared folder exists
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))

    step(5, 'Upload files to TEST_RESHARE_SUBFOLDER/SUB')

    shared = reflection.getSharedObject()
    createfile(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'), '04', count=100, bs=10)
    shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'] = md5sum(
        os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'))

    run_ocsync(d, user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)

    step(6, 'Resync and check')

    run_ocsync(d, user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FOLDER'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FILE.dat'))
    expect_does_not_exist(os.path.join(d, 'TEST_RESHARE_FILE.dat'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])

    step(8, 'Resync and check')

    run_ocsync(d, user_num=2, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FOLDER'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FILE.dat'))
    expect_does_not_exist(os.path.join(d, 'TEST_RESHARE_FILE.dat'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])


@add_worker
def recipient3(step):
    if finish_if_not_capable():
        return

    user = '%s%i' % (config.oc_account_name, 3)

    step (2, 'Create workdir')
    d = make_workdir()

    group2 = get_group_name(2)
    step(3, 'Reshare /TEST_RESHARE_FILE.dat with %s' % (group2))

    client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
    client.login(user, config.oc_account_password)
    # only the first user of the group shares with another group, to keep it simple
    share1_data = client.share_file_with_group('/TEST_RESHARE_FILE.dat', group2, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (group2))


    step(4, 'Sync and check required files')

    run_ocsync(d, user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that shared folder exists
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))

    # Check that shared file exist
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])

    step(5, 'Change file TEST_RESHARE_FILE')

    modify_file(os.path.join(d, 'TEST_RESHARE_FILE.dat'), '10', count=100, bs=10)
    shared['TEST_RESHARE_FILE'] = md5sum(
        os.path.join(d, 'TEST_RESHARE_FILE.dat'))

    run_ocsync(d, user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)

    step(6, 'Resync and check')

    run_ocsync(d, user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FOLDER'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FILE.dat'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])

    step(8, 'Resync and check')

    run_ocsync(d, user_num=3, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FOLDER'))
    expect_does_not_exist(os.path.join(d, 'TEST_SHARE_FILE.dat'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'TEST_RESHARE_SUBFOLDER_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_SUBFOLDER', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])
    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])

@add_worker
def recipient4(step):
    if finish_if_not_capable():
        return

    user = '%s%i' % (config.oc_account_name, 4)

    step (2, 'Create workdir')
    d = make_workdir()

    step(6, 'Initialize share mounts (sync and check)')

    run_ocsync(d, user_num=4, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'SUB'))
    expect_exists(os.path.join(d, 'TEST_SHARE_FOLDER'))
    expect_does_not_exist(os.path.join(d, 'TEST_RESHARE_SUBFOLDER'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()

    expect_not_modified(os.path.join(d, 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'),
                        shared['TEST_SHARE_FOLDER_FILE'])

    expect_not_modified(os.path.join(d, 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])

    expect_not_modified(os.path.join(d, 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])

    expect_not_modified(os.path.join(d, 'TEST_SHARE_FILE.dat'), shared['TEST_SHARE_FILE'])

    step(8, 'Create SHARED_ITEMS and RESHARED_ITEMS folder and move relevant files there')

    mkdir(os.path.join(d, 'SHARED_ITEMS'))
    mkdir(os.path.join(d, 'RESHARED_ITEMS'))

    mv(os.path.join(d, 'TEST_SHARE_FOLDER'), (os.path.join(d, 'SHARED_ITEMS')))
    mv(os.path.join(d, 'TEST_SHARE_FILE.dat'), (os.path.join(d, 'SHARED_ITEMS')))

    mv(os.path.join(d, 'TEST_RESHARE_FILE.dat'), (os.path.join(d, 'RESHARED_ITEMS')))
    mv(os.path.join(d, 'SUB'), (os.path.join(d, 'RESHARED_ITEMS')))

    run_ocsync(d, user_num=4, use_new_dav_endpoint=use_new_dav_endpoint)

    step(10, 'Sync and check')

    run_ocsync(d, user_num=4, use_new_dav_endpoint=use_new_dav_endpoint)

    # Check that folders have been synced down correctly
    expect_exists(os.path.join(d, 'RESHARED_ITEMS', 'SUB'))
    expect_exists(os.path.join(d, 'SHARED_ITEMS', 'TEST_SHARE_FOLDER'))
    expect_does_not_exist(os.path.join(d, 'TEST_RESHARE_SUBFOLDER'))

    # Check that files have been synced down correctly
    shared = reflection.getSharedObject()

    expect_not_modified(os.path.join(d, 'SHARED_ITEMS', 'TEST_SHARE_FOLDER', 'TEST_SHARE_FOLDER_FILE.dat'),
                        shared['TEST_SHARE_FOLDER_FILE'])

    expect_not_modified(os.path.join(d, 'RESHARED_ITEMS', 'SUB', 'TEST_RESHARE_SUBFOLDER_SUB_FILE.dat'),
                        shared['TEST_RESHARE_SUBFOLDER_SUB_FILE'])

    expect_not_modified(os.path.join(d, 'RESHARED_ITEMS', 'TEST_RESHARE_FILE.dat'), shared['TEST_RESHARE_FILE'])

    expect_not_modified(os.path.join(d, 'SHARED_ITEMS', 'TEST_SHARE_FILE.dat'), shared['TEST_SHARE_FILE'])
