__doc__ = """
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| step  | owner           | R1             | R2                | R3          | R4              |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 2     | create dir      | create dir     | create dir        | create dir  | create dir      |
|       | share /test     |                |                   |             |                 |
|       |   -> R1 R2      |                |                   |             |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 3     |                 |                | reshare /test     |             |                 |
|       |                 |                |   -> R3           |             |                 |
|       |                 |                | reshare /test/sub |             |                 |
|       |                 |                |   -> R4           |             |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 4     | get etags       | get etags      | get etags         | get etags   | get etags       |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 5     | upload to       |                |                   |             |                 |
|       |   -> /test      |                |                   |             |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 6     | propagation     | propagation    | propagation       | propagation | NOT propagation |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 7     |                 |                | upload to         |             |                 |
|       |                 |                |   -> /test        |             |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 8     | propagation     | propagation    | propagation       | propagation | NOT propagation |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 9     | upload to       |                |                   |             |                 |
|       |   -> /test/sub  |                |                   |             |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 10    | propagation     | propagation    | propagation       | propagation | propagation     |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 11    |                 | upload to      |                   |             |                 |
|       |                 |   -> /test/sub |                   |             |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 12    | propagation     | propagation    | propagation       | propagation | propagation     |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 13    |                 |                |                   |             | upload to /sub  |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 14    | propagation     | propagation    | propagation       | propagation | propagation     |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 15    |                 |                | unshare           |             |                 |
|       |                 |                |   -> /test/sub    |             |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
| 16    | NOT propagation | NOT            | NOT propagation   | NOT         | propagation     |
|       |                 | propagation    |                   | propagation |                 |
+-------+-----------------+----------------+-------------------+-------------+-----------------+
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

def compare_list(list1, list2, func):
    """
    Compare the list item by item using the function func. If func returns False, compare list
    will return False
    """
    if len(list1) != len(list2):
        return False

    for index in range(0, len(list1)):
        if not func(list1[index], list2[index]):
            return False
    return True

def get_client_etags(clients, path):
    new_etags = []
    for client in clients:
        new_etags.append(client.file_info(path).get_etag())

    return new_etags

def run_group_ocsync(d, group_name):
    for usernum in group_map[group_name]:
        run_ocsync(os.path.join(d, str(usernum)), user_num=usernum, use_new_dav_endpoint=use_new_dav_endpoint)

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

@add_worker
def owner(step):
    if finish_if_not_capable():
        return

    user = '%s%i' % (config.oc_account_name, 1)

    step (2, 'Create workdir')
    d = make_workdir()

    mkdir(os.path.join(d, 'test', 'sub'))
    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
    client.login(user, config.oc_account_password)
    # make sure folder is shared
    group1 = get_group_name(1)
    share1_data = client.share_file_with_group('/test', group1, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (group1,))

    group2 = get_group_name(2)
    share2_data = client.share_file_with_group('/test', group2, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (group2,))

    step(4, 'get base etags to compare')
    root_etag = client.file_info('/').get_etag()
    test_etag = client.file_info('/test').get_etag()

    step(5, 'Upload to /test')
    createfile(os.path.join(d, 'test', 'test2.txt'), '2', count=1000, bs=10)
    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    step(6, 'verify etag propagation')
    root_etag2 = client.file_info('/').get_etag()
    error_check(root_etag != root_etag2, 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag2))

    step(8, 'verify etag propagation')
    root_etag3 = client.file_info('/').get_etag()
    error_check(root_etag2 != root_etag3, 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag2, root_etag3))

    step(9, 'Upload to /test/sub')
    createfile(os.path.join(d, 'test', 'sub', 'test4.txt'), '4', count=1000, bs=10)
    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    step(10, 'verify etag propagation')
    root_etag4 = client.file_info('/').get_etag()
    test_etag2 = client.file_info('/test').get_etag()
    error_check(root_etag3 != root_etag4, 'owner uploads to /test/sub/test4.txt '
                'etag for / previous [%s] new [%s]' % (root_etag3, root_etag4))
    error_check(test_etag != test_etag2, 'owner uploads to /test/sub/test4.txt '
                'etag for /test previous [%s] new [%s]' % (test_etag, test_etag2))

    step(12, 'verify etag propagation')
    root_etag5 = client.file_info('/').get_etag()
    test_etag3 = client.file_info('/test').get_etag()
    error_check(root_etag4 != root_etag5, 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for / previous [%s] new [%s]' % (root_etag4, root_etag5))
    error_check(test_etag2 != test_etag3, 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for /test previous [%s] new [%s]' % (test_etag2, test_etag3))

    step(14, 'verify etag propagation')
    root_etag6 = client.file_info('/').get_etag()
    test_etag4 = client.file_info('/test').get_etag()
    error_check(root_etag5 != root_etag6, 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etag5, root_etag6))
    error_check(test_etag3 != test_etag4, 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for /test previous [%s] new [%s]' % (test_etag3, test_etag4))

    step(16, 'verify etag is NOT propagated')
    root_etag7 = client.file_info('/').get_etag()
    test_etag5 = client.file_info('/test').get_etag()
    error_check(root_etag6 == root_etag7, 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))
    error_check(test_etag4 == test_etag5, 'recipient 2 unshares reshare '
                'etag for /test previous [%s] new [%s]' % (test_etag4, test_etag5))

@add_worker
def recipient1(step):
    if finish_if_not_capable():
        return

    group = get_group_name(1)

    step (2, 'Create workdir')

    d = make_workdir()
    for usernum in group_map[group]:
        mkdir(os.path.join(d, str(usernum)))

    run_group_ocsync(d, group)

    clients = []
    for usernum in group_map[group]:
        client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
        client.login(get_account_name(usernum), config.oc_account_password)
        clients.append(client)

    step(4, 'get base etags to compare')
    root_etags = get_client_etags(clients, '/')
    test_etags = get_client_etags(clients, '/test')

    step(6, 'verify etag propagation')
    root_etags2 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags, root_etags2, op.ne), 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etags, root_etags2))

    step(8, 'verify etag propagation')
    root_etags3 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags2, root_etags3, op.ne), 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etags2, root_etags3))

    step(10, 'verify etag propagation')
    root_etags4 = get_client_etags(clients, '/')
    test_etags2 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags3, root_etags4, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for / previous [%s] new [%s]' % (root_etags3, root_etags4))
    error_check(compare_list(test_etags, test_etags2, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for /test previous [%s] new [%s]' % (test_etags, test_etags2))

    step(11, 'Upload to /test/sub')
    run_group_ocsync(d, group)
    createfile(os.path.join(d, str(group_map[group][0]), 'test', 'sub', 'test5.txt'), '5', count=1000, bs=10)
    run_group_ocsync(d, group)

    step(12, 'verify etag propagation')
    root_etags5 = get_client_etags(clients, '/')
    test_etags3 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags4, root_etags5, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for / previous [%s] new [%s]' % (root_etags4, root_etags5))
    error_check(compare_list(test_etags2, test_etags3, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for /test previous [%s] new [%s]' % (test_etags2, test_etags3))

    step(14, 'verify etag propagation')
    root_etags6 = get_client_etags(clients, '/')
    test_etags4 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags5, root_etags6, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etags5, root_etags6))
    error_check(compare_list(test_etags3, test_etags4, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for /test previous [%s] new [%s]' % (test_etags3, test_etags4))

    step(16, 'verify etag propagation')
    root_etags7 = get_client_etags(clients, '/')
    test_etags5 = get_client_etags(clients, '/test')
    # not affected by the unshare
    error_check(compare_list(root_etags6, root_etags7, op.eq), 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etags6, root_etags7))
    error_check(compare_list(test_etags4, test_etags5, op.eq), 'recipient 2 unshares reshare '
                'etag for /test previous [%s] new [%s]' % (test_etags4, test_etags5))

@add_worker
def recipient2(step):
    if finish_if_not_capable():
        return

    group = get_group_name(2)

    step (2, 'Create workdir')

    d = make_workdir()
    for usernum in group_map[group]:
        mkdir(os.path.join(d, str(usernum)))

    run_group_ocsync(d, group)

    clients = []
    for usernum in group_map[group]:
        client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
        client.login(get_account_name(usernum), config.oc_account_password)
        clients.append(client)

    group3 = get_group_name(3)
    group4 = get_group_name(4)

    step(3, 'Reshare /test folder with %s and /test/sub with %s' % (group3, group4))

    # only the first user of the group shares with another group, to keep it simple
    share1_data = clients[0].share_file_with_group('/test', group3, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (group3,))
    share2_data = clients[0].share_file_with_group('/test/sub', group4, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (group4,))

    step(4, 'get base etags to compare')
    root_etags = get_client_etags(clients, '/')
    test_etags = get_client_etags(clients, '/test')

    step(6, 'verify etag propagation')
    root_etags2 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags, root_etags2, op.ne), 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etags, root_etags2))

    step(7, 'Upload to /test')
    run_group_ocsync(d, group)
    createfile(os.path.join(d, str(group_map[group][0]), 'test', 'test3.txt'), '3', count=1000, bs=10)
    run_group_ocsync(d, group)

    step(8, 'verify etag propagation')
    root_etags3 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags2, root_etags3, op.ne), 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etags2, root_etags3))

    step(10, 'verify etag propagation')
    root_etags4 = get_client_etags(clients, '/')
    test_etags2 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags3, root_etags4, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for / previous [%s] new [%s]' % (root_etags3, root_etags4))
    error_check(compare_list(test_etags, test_etags2, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for /test previous [%s] new [%s]' % (test_etags, test_etags2))

    step(12, 'verify etag propagation')
    root_etags5 = get_client_etags(clients, '/')
    test_etags3 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags4, root_etags5, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for / previous [%s] new [%s]' % (root_etags4, root_etags5))
    error_check(compare_list(test_etags2, test_etags3, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for /test previous [%s] new [%s]' % (test_etags2, test_etags3))

    step(14, 'verify etag propagation')
    root_etags6 = get_client_etags(clients, '/')
    test_etags4 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags5, root_etags6, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etags5, root_etags6))
    error_check(compare_list(test_etags3, test_etags4, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for /test previous [%s] new [%s]' % (test_etags3, test_etags4))

    step(15, 'Unshare reshared /test/sub')
    clients[0].delete_share(share2_data.share_id)

    step(16, 'verify etag propagation')
    root_etags7 = get_client_etags(clients, '/')
    test_etags5 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags6, root_etags7, op.eq), 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etags6, root_etags7))
    error_check(compare_list(test_etags4, test_etags5, op.eq), 'recipient 2 unshares reshare '
                'etag for /test previous [%s] new [%s]' % (test_etags4, test_etags5))

@add_worker
def recipient3(step):
    if finish_if_not_capable():
        return

    group = get_group_name(3)

    step (2, 'Create workdir')

    d = make_workdir()
    for usernum in group_map[group]:
        mkdir(os.path.join(d, str(usernum)))

    run_group_ocsync(d, group)

    clients = []
    for usernum in group_map[group]:
        client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
        client.login(get_account_name(usernum), config.oc_account_password)
        clients.append(client)

    step(4, 'get base etags to compare')
    root_etags = get_client_etags(clients, '/')
    test_etags = get_client_etags(clients, '/test')

    step(6, 'verify etag propagation')
    root_etags2 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags, root_etags2, op.ne), 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etags, root_etags2))

    step(8, 'verify etag propagation')
    root_etags3 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags2, root_etags3, op.ne), 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etags2, root_etags3))

    step(10, 'verify etag propagation')
    root_etags4 = get_client_etags(clients, '/')
    test_etags2 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags3, root_etags4, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for / previous [%s] new [%s]' % (root_etags3, root_etags4))
    error_check(compare_list(test_etags, test_etags2, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for /test previous [%s] new [%s]' % (test_etags, test_etags2))

    step(12, 'verify etag propagation')
    root_etags5 = get_client_etags(clients, '/')
    test_etags3 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags4, root_etags5, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for / previous [%s] new [%s]' % (root_etags4, root_etags5))
    error_check(compare_list(test_etags2, test_etags3, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for /test previous [%s] new [%s]' % (test_etags2, test_etags3))

    step(14, 'verify etag propagation')
    root_etags6 = get_client_etags(clients, '/')
    test_etags4 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags5, root_etags6, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etags5, root_etags6))
    error_check(compare_list(test_etags3, test_etags4, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for /test previous [%s] new [%s]' % (test_etags3, test_etags4))

    step(16, 'verify etag propagation')
    root_etags7 = get_client_etags(clients, '/')
    test_etags5 = get_client_etags(clients, '/test')
    error_check(compare_list(root_etags6, root_etags7, op.eq), 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etags6, root_etags7))
    error_check(compare_list(test_etags4, test_etags5, op.eq), 'recipient 2 unshares reshare '
                'etag for /test previous [%s] new [%s]' % (test_etags4, test_etags5))

@add_worker
def recipient4(step):
    if finish_if_not_capable():
        return

    group = get_group_name(4)

    step (2, 'Create workdir')

    d = make_workdir()
    for usernum in group_map[group]:
        mkdir(os.path.join(d, str(usernum)))

    run_group_ocsync(d, group)

    clients = []
    for usernum in group_map[group]:
        client = get_oc_api(use_new_dav_endpoint=use_new_dav_endpoint)
        client.login(get_account_name(usernum), config.oc_account_password)
        clients.append(client)

    step(4, 'get base etags to compare')
    root_etags = get_client_etags(clients, '/')
    sub_etags = get_client_etags(clients, '/sub')

    step(6, 'verify etag is NOT propagated')
    root_etags2 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags, root_etags2, op.eq), 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etags, root_etags2))

    step(8, 'verify etag is NOT propagated')
    root_etags3 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags2, root_etags3, op.eq), 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etags2, root_etags3))

    step(10, 'verify etag propagation')
    root_etags4 = get_client_etags(clients, '/')
    sub_etags2 = get_client_etags(clients, '/sub')
    error_check(compare_list(root_etags3, root_etags4, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for / previous [%s] new [%s]' % (root_etags3, root_etags4))
    error_check(compare_list(sub_etags, sub_etags2, op.ne), 'owner uploads to /test/sub/test4.txt '
                'etag for /sub previous [%s] new [%s]' % (sub_etags, sub_etags2))

    step(12, 'verify etag propagation')
    root_etags5 = get_client_etags(clients, '/')
    sub_etags3 = get_client_etags(clients, '/sub')
    error_check(compare_list(root_etags4, root_etags5, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for / previous [%s] new [%s]' % (root_etags4, root_etags5))
    error_check(compare_list(sub_etags2, sub_etags3, op.ne), 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for /sub previous [%s] new [%s]' % (sub_etags2, sub_etags3))

    step(13, 'Upload to /sub')
    run_group_ocsync(d, group)
    createfile(os.path.join(d, str(group_map[group][0]), 'sub', 'test6.txt'), '6', count=1000, bs=10)
    run_group_ocsync(d, group)

    step(14, 'verify etag propagation')
    root_etags6 = get_client_etags(clients, '/')
    sub_etags4 = get_client_etags(clients, '/sub')
    error_check(compare_list(root_etags5, root_etags6, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etags5, root_etags6))
    error_check(compare_list(sub_etags3, sub_etags4, op.ne), 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for /sub previous [%s] new [%s]' % (sub_etags3, sub_etags4))

    step(16, 'verify etag propagation')
    root_etags7 = get_client_etags(clients, '/')
    error_check(compare_list(root_etags6, root_etags7, op.ne), 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etags6, root_etags7))
    # /sub folder should be deleted at this point, so no checking

