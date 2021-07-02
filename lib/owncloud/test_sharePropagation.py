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

def parse_worker_number(worker_name):
    match = re.search(r'(\d+)$', worker_name)
    if match is not None:
        return int(match.group())
    else:
        return None

@add_worker
def setup(step):

    step(1, 'create test users')

    num_users = 4

    # Create additional accounts
    if config.oc_number_test_users < num_users:
            for i in range(config.oc_number_test_users + 1, num_users + 1):
                username = "%s%i" % (config.oc_account_name, i)
                delete_owncloud_account(username)
                create_owncloud_account(username, config.oc_account_password)
                login_owncloud_account(username, config.oc_account_password)

    check_users(num_users)

@add_worker
def owner(step):

    user = '%s%i' % (config.oc_account_name, 1)

    step (2, 'Create workdir')
    d = make_workdir()

    mkdir(os.path.join(d, 'test', 'sub'))
    run_ocsync(d, user_num=1)

    client = get_oc_api()
    client.login(user, config.oc_account_password)
    # make sure folder is shared
    user2 = '%s%i' % (config.oc_account_name, 2)
    share1_data = client.share_file_with_user('/test', user2, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (user2,))

    user3 = '%s%i' % (config.oc_account_name, 3)
    share2_data = client.share_file_with_user('/test', user3, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (user3,))

    root_etag = client.file_info('/').get_etag()

    step(3, 'Upload file')
    createfile(os.path.join(d, 'test', 'test.txt'), '1', count=1000, bs=10)
    run_ocsync(d, user_num=1)

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
    share1_data = client.share_file_with_user('/test', user2, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (user2,))
    share2_data = client.share_file_with_user('/test', user3, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (user3,))

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

    usernum = parse_worker_number(reflection.getProcessName())
    user = '%s%i' % (config.oc_account_name, usernum)

    step (2, 'Create workdir')

    d = make_workdir()
    run_ocsync(d, user_num=usernum)

    client = get_oc_api()
    client.login(user, config.oc_account_password)
    root_etag = client.file_info('/').get_etag()

    step(4, 'verify etag propagation')
    run_ocsync(d, user_num=usernum)

    root_etag2 = client.file_info('/').get_etag()
    error_check(root_etag != root_etag2, 'owner uploads /test/test.txt '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag2))

    step(5, 'upload to shared folder')
    if usernum is 2:
        createfile(os.path.join(d, 'test', 'test2.txt'), '2', count=1000, bs=10)
        run_ocsync(d, user_num=usernum)

    step(6, 'verify another etag propagation')
    root_etag3 = client.file_info('/').get_etag()
    error_check(root_etag2 != root_etag3, 'recipients upload to /test/test2.txt'
                'etag for / previous [%s] new [%s]' % (root_etag2, root_etag3))

    step(8, 'verify etag propagation')
    root_etag4 = client.file_info('/').get_etag()
    error_check(root_etag3 != root_etag4, 'owner unshares '
                'etag for / previous [%s] new [%s]' % (root_etag3, root_etag4))

    step(10, 'reshare file')
    if usernum is 2:
        user4 = '%s%i' % (config.oc_account_name, 4)
        share_data = client.share_file_with_user('/test', user4, perms=31)

    step(11, 'verify etag propagation')
    root_etag5 = client.file_info('/').get_etag()
    error_check(root_etag4 != root_etag5, 'recipient 2 reshares /test to recipient 4 '
                'etag for / previous [%s] new [%s]' % (root_etag4, root_etag5))

    step(12, 'recipient 2 upload a file')
    if usernum is 2:
        createfile(os.path.join(d, 'test', 'test3.txt'), '3', count=1000, bs=10)
        run_ocsync(d, user_num=usernum)

    step(13, 'verify etag propagation')
    root_etag6 = client.file_info('/').get_etag()
    error_check(root_etag5 != root_etag6, 'recipient 2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag5, root_etag6))

    step(15, 'verify etag propagation')
    root_etag7 = client.file_info('/').get_etag()
    error_check(root_etag6 != root_etag7, 'recipient 4 uploads /test/test4.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))

    step(16, 'unshare file')
    if usernum is 2:
        client.delete_share(share_data.share_id)

    step(17, 'verify etag propagation')
    root_etag8 = client.file_info('/').get_etag()
    # recipients 2 and 3 aren't affected by the unshare
    error_check(root_etag7 == root_etag8, 'recipient 2 unshares the reshare '
                'etag for / previous [%s] new [%s]' % (root_etag7, root_etag8))

@add_worker
def recipient_4(step):
    usernum = parse_worker_number(reflection.getProcessName())
    user = '%s%i' % (config.oc_account_name, usernum)

    step (2, 'Create workdir')

    d = make_workdir()
    run_ocsync(d, user_num=usernum)

    client = get_oc_api()
    client.login(user, config.oc_account_password)
    root_etag = client.file_info('/').get_etag()

    step(11, 'verify etag propagation')
    root_etag5 = client.file_info('/').get_etag()
    error_check(root_etag != root_etag5, 'recipient 2 reshares /test to recipient 4 '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag5))

    step(13, 'verify etag propagation')
    root_etag6 = client.file_info('/').get_etag()
    error_check(root_etag5 != root_etag6, 'recipient 2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag5, root_etag6))

    step(14, 'upload file')
    run_ocsync(d, user_num=usernum)
    createfile(os.path.join(d, 'test', 'test4.txt'), '4', count=1000, bs=10)
    run_ocsync(d, user_num=usernum)

    step(15, 'verify etag propagation')
    root_etag7 = client.file_info('/').get_etag()
    error_check(root_etag6 != root_etag7, 'recipient 4 uploads /test/test4.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))

    step(17, 'verify etag propagation')
    root_etag8 = client.file_info('/').get_etag()
    error_check(root_etag7 != root_etag8, 'recipient 2 unshares the reshare '
                'etag for / previous [%s] new [%s]' % (root_etag7, root_etag8))

for i in range(2,4):
    add_worker(recipients, name='recipient_%s' % (i,))

