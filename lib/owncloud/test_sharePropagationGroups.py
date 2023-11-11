__doc__ = """
Test share etag propagation

+-------------+-------------------------+-------------------------+----------------------+
| step number | owner                   | R2 R3                   | R4                   |
+-------------+-------------------------+-------------------------+----------------------+
| 2           | create working dir      | create working dir      | create working dir   |
|             | share folder with R2 R3 |                         |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 3           | sync                    |                         |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 4           | verify propagation      | verify propagation      |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 5           |                         | upload in shared dir    |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 6           | verify propagation      | verify propagation      |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 7           | unshare folder          |                         |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 8           | verify etag is the same | verify propagation      |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 9           | share folder with R2 R3 |                         |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 10          |                         | R2 reshare with R4      |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 11          | verify etag is the same | verify propagation      | verify propagation   |
+-------------+-------------------------+-------------------------+----------------------+
| 12          |                         | R2 upload in shared dir |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 13          | verify propagation      | verify propagation      | verify propagation   |
+-------------+-------------------------+-------------------------+----------------------+
| 14          |                         |                         | upload in shared dir |
+-------------+-------------------------+-------------------------+----------------------+
| 15          | verify propagation      | verify propagation      | verify propagation   |
+-------------+-------------------------+-------------------------+----------------------+
| 16          |                         | R2 unshares folder      |                      |
+-------------+-------------------------+-------------------------+----------------------+
| 17          | verify etag is the same | verify etag is the same | verify propagation   |
+-------------+-------------------------+-------------------------+----------------------+
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

def get_client_etags(clients):
    new_etags = []
    for client in clients:
        new_etags.append(client.file_info('/').get_etag())

    return new_etags

def run_group_ocsync(d, group_name):
    for usernum in group_map[group_name]:
        run_ocsync(os.path.join(d, str(usernum)), user_num=usernum, use_new_dav_endpoint=use_new_dav_endpoint)

def parse_worker_number(worker_name):
    match = re.search(r'(\d+)$', worker_name)
    if match is not None:
        return int(match.group())
    else:
        return None

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
    num_users = 7

    # Create additional accounts
    if config.oc_number_test_users < num_users:
            for i in range(config.oc_number_test_users + 1, num_users + 1):
                username = "%s%i" % (config.oc_account_name, i)
                delete_owncloud_account(username)
                create_owncloud_account(username, config.oc_account_password)
                login_owncloud_account(username, config.oc_account_password)

    check_users(num_users)
    reset_owncloud_group(num_groups=3)

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

    root_etag = client.file_info('/').get_etag()

    step(3, 'Upload file')
    createfile(os.path.join(d, 'test', 'test.txt'), '1', count=1000, bs=10)
    run_ocsync(d, user_num=1, use_new_dav_endpoint=use_new_dav_endpoint)

    step(4, 'Verify etag propagation')
    root_etag2 = client.file_info('/').get_etag()
    error_check(root_etag != root_etag2, 'owner uploads /test/test.txt '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag2))

    step(6, 'verify another etag propagation')
    root_etag3 = client.file_info('/').get_etag()
    error_check(root_etag2 != root_etag3, 'recipients upload to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etag2, root_etag3))

    step(7, 'unshare')
    client.delete_share(share1_data.share_id)
    client.delete_share(share2_data.share_id)

    step(8, 'verify etag propagation')
    root_etag4 = client.file_info('/').get_etag()
    error_check(root_etag3 == root_etag4, 'owner unshares '
                'etag for / previous [%s] new [%s]' % (root_etag3, root_etag4))

    step(9, 'share again the files')
    share1_data = client.share_file_with_group('/test', group1, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (group1,))
    share2_data = client.share_file_with_group('/test', group2, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (group2,))

    step(11, 'verify etag propagation')
    root_etag5 = client.file_info('/').get_etag()
    error_check(root_etag4 == root_etag5, 'recipient 2 reshares /test to recipient 4 '
                'etag for / previous [%s] new [%s]' % (root_etag4, root_etag5))

    step(13, 'verify etag propagation')
    root_etag6 = client.file_info('/').get_etag()
    error_check(root_etag5 != root_etag6, 'recipient 2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag5, root_etag6))

    step(15, 'verify etag propagation')
    root_etag7 = client.file_info('/').get_etag()
    error_check(root_etag6 != root_etag7, 'recipient 4 uploads /test/test4.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))

    step(17, 'verify etag is the same')
    root_etag8 = client.file_info('/').get_etag()
    # It shoudn't be propagated here in this case
    error_check(root_etag7 == root_etag8, 'recipient 2 unshares the reshare '
                'etag for / previous [%s] new [%s]' % (root_etag7, root_etag8))

def recipients(step):
    if finish_if_not_capable():
        return

    groupnum = parse_worker_number(reflection.getProcessName())
    group = get_group_name(groupnum)

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

    root_etags = get_client_etags(clients)

    step(4, 'verify etag propagation')
    run_group_ocsync(d, group)

    root_etags2 = get_client_etags(clients)
    error_check(compare_list(root_etags, root_etags2, op.ne), 'owner uploads /test/test.txt '
                'etag for / previous [%s] new [%s]' % (root_etags, root_etags2))

    step(5, 'upload to shared folder')
    # Create a file just in one of the users of the group
    if groupnum is 1:
        createfile(os.path.join(d, str(group_map[group][0]), 'test', 'test2.txt'), '2', count=1000, bs=10)
        # the group sync is done sequentially so there shouldn't be issues syncing
        run_group_ocsync(d, group)

    step(6, 'verify another etag propagation')
    if groupnum is not 1:
        run_group_ocsync(d, group)
    root_etags3 = get_client_etags(clients)
    error_check(compare_list(root_etags2, root_etags3, op.ne), 'recipients upload to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etags2, root_etags3))

    step(8, 'verify etag propagation')
    root_etags4 = get_client_etags(clients)
    error_check(compare_list(root_etags3, root_etags4, op.ne), 'owner unshares '
                'etag for / previous [%s] new [%s]' % (root_etags3, root_etags4))

    step(10, 'reshare file')
    if groupnum is 1:
        # first user of the group1 reshares /test to group
        share_data = clients[0].share_file_with_group('/test', get_group_name(3), perms=31)

    step(11, 'verify etag propagation')
    root_etags5 = get_client_etags(clients)
    error_check(compare_list(root_etags4, root_etags5, op.ne), 'recipient 2 reshares /test to recipient 4 '
                'etag for / previous [%s] new [%s]' % (root_etags4, root_etags5))

    step(12, 'recipient 2 upload a file')
    if groupnum is 1:
        createfile(os.path.join(d, str(group_map[group][0]), 'test', 'test3.txt'), '3', count=1000, bs=10)
        run_group_ocsync(d, group)

    step(13, 'verify etag propagation')
    if groupnum is not 1:
        run_group_ocsync(d, group)
    root_etags6 = get_client_etags(clients)
    error_check(compare_list(root_etags5, root_etags6, op.ne), 'recipient 2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etags5, root_etags6))

    step(15, 'verify etag propagation')
    root_etags7 = get_client_etags(clients)
    error_check(compare_list(root_etags6, root_etags7, op.ne), 'recipient 4 uploads /test/test4.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etags6, root_etags7))

    step(16, 'unshare file')
    if groupnum is 1:
        # remove the reshare created before
        clients[0].delete_share(share_data.share_id)

    step(17, 'verify etag propagation')
    root_etags8 = get_client_etags(clients)
    # recipients 2 and 3 aren't affected by the unshare
    error_check(compare_list(root_etags7, root_etags8, op.eq), 'recipient 2 unshares the reshare '
                'etag for / previous [%s] new [%s]' % (root_etags7, root_etags8))

@add_worker
def recipient_3(step):
    if finish_if_not_capable():
        return

    groupnum = parse_worker_number(reflection.getProcessName())
    group = get_group_name(groupnum)

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

    root_etags = get_client_etags(clients)

    step(11, 'verify etag propagation')
    root_etags5 = get_client_etags(clients)
    error_check(compare_list(root_etags, root_etags5, op.ne), 'recipient 2 reshares /test to recipient 4 '
                'etag for / previous [%s] new [%s]' % (root_etags, root_etags5))

    step(13, 'verify etag propagation')
    root_etags6 = get_client_etags(clients)
    error_check(compare_list(root_etags5, root_etags6, op.ne), 'recipient 2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etags5, root_etags6))
    run_group_ocsync(d, group)

    step(14, 'upload file')
    # just the first first user of the group uploads the file
    createfile(os.path.join(d, str(group_map[group][0]), 'test', 'test4.txt'), '4', count=1000, bs=10)
    run_group_ocsync(d, group)

    step(15, 'verify etag propagation')
    root_etags7 = get_client_etags(clients)
    error_check(compare_list(root_etags6, root_etags7, op.ne), 'recipient 4 uploads /test/test4.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etags6, root_etags7))

    step(17, 'verify etag propagation')
    root_etags8 = get_client_etags(clients)
    error_check(compare_list(root_etags7, root_etags8, op.ne), 'recipient 2 unshares the reshare '
                'etag for / previous [%s] new [%s]' % (root_etags7, root_etags8))

for i in range(1,3):
    add_worker(recipients, name='recipients_%s' % (i,))

