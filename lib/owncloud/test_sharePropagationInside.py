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

@add_worker
def setup(step):

    step(1, 'create test users')

    num_users = 5

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
    share1_data = client.share_file_with_user('/test', user3, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (user3,))

    step(4, 'get base etags to compare')
    root_etag = client.file_info('/').get_etag()
    test_etag = client.file_info('/test').get_etag()

    step(5, 'Upload to /test')
    createfile(os.path.join(d, 'test', 'test2.txt'), '2', count=1000, bs=10)
    run_ocsync(d, user_num=1)

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
    run_ocsync(d, user_num=1)

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

    user = '%s%i' % (config.oc_account_name, 2)

    step (2, 'Create workdir')

    d = make_workdir()
    run_ocsync(d, user_num=2)

    client = get_oc_api()
    client.login(user, config.oc_account_password)

    step(4, 'get base etags to compare')
    root_etag = client.file_info('/').get_etag()
    test_etag = client.file_info('/test').get_etag()

    step(6, 'verify etag propagation')
    root_etag2 = client.file_info('/').get_etag()
    error_check(root_etag != root_etag2, 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag2))

    step(8, 'verify etag propagation')
    root_etag3 = client.file_info('/').get_etag()
    error_check(root_etag2 != root_etag3, 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag2, root_etag3))

    step(10, 'verify etag propagation')
    root_etag4 = client.file_info('/').get_etag()
    test_etag2 = client.file_info('/test').get_etag()
    error_check(root_etag3 != root_etag4, 'owner uploads to /test/sub/test4.txt '
                'etag for / previous [%s] new [%s]' % (root_etag3, root_etag4))
    error_check(test_etag != test_etag2, 'owner uploads to /test/sub/test4.txt '
                'etag for /test previous [%s] new [%s]' % (test_etag, test_etag2))

    step(11, 'Upload to /test/sub')
    run_ocsync(d, user_num=2)
    createfile(os.path.join(d, 'test', 'sub', 'test5.txt'), '5', count=1000, bs=10)
    run_ocsync(d, user_num=2)

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

    step(16, 'verify etag propagation')
    root_etag7 = client.file_info('/').get_etag()
    test_etag5 = client.file_info('/test').get_etag()
    # not affected by the unshare
    error_check(root_etag6 == root_etag7, 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))
    error_check(test_etag4 == test_etag5, 'recipient 2 unshares reshare '
                'etag for /test previous [%s] new [%s]' % (test_etag4, test_etag5))

@add_worker
def recipient2(step):

    user = '%s%i' % (config.oc_account_name, 3)

    step (2, 'Create workdir')

    d = make_workdir()
    run_ocsync(d, user_num=3)

    client = get_oc_api()
    client.login(user, config.oc_account_password)
    root_etag = client.file_info('/').get_etag()

    user4 = '%s%i' % (config.oc_account_name, 4)
    user5 = '%s%i' % (config.oc_account_name, 5)

    step(3, 'Reshare /test folder with %s and /test/sub with %s' % (user4, user5))

    share1_data = client.share_file_with_user('/test', user4, perms=31)
    fatal_check(share1_data, 'failed sharing a file with %s' % (user4,))
    share2_data = client.share_file_with_user('/test/sub', user5, perms=31)
    fatal_check(share2_data, 'failed sharing a file with %s' % (user5,))

    step(4, 'get base etags to compare')
    root_etag = client.file_info('/').get_etag()
    test_etag = client.file_info('/test').get_etag()

    step(6, 'verify etag propagation')
    root_etag2 = client.file_info('/').get_etag()
    error_check(root_etag != root_etag2, 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag2))

    step(7, 'Upload to /test')
    run_ocsync(d, user_num=3)
    createfile(os.path.join(d, 'test', 'test3.txt'), '3', count=1000, bs=10)
    run_ocsync(d, user_num=3)

    step(8, 'verify etag propagation')
    root_etag3 = client.file_info('/').get_etag()
    error_check(root_etag2 != root_etag3, 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag2, root_etag3))

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

    step(15, 'Unshare reshared /test/sub')
    client.delete_share(share2_data.share_id)

    step(16, 'verify etag propagation')
    root_etag7 = client.file_info('/').get_etag()
    test_etag5 = client.file_info('/test').get_etag()
    error_check(root_etag6 == root_etag7, 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))
    error_check(test_etag4 == test_etag5, 'recipient 2 unshares reshare '
                'etag for /test previous [%s] new [%s]' % (test_etag4, test_etag5))

@add_worker
def recipient3(step):

    user = '%s%i' % (config.oc_account_name, 4)

    step (2, 'Create workdir')

    d = make_workdir()
    run_ocsync(d, user_num=4)

    client = get_oc_api()
    client.login(user, config.oc_account_password)

    step(4, 'get base etags to compare')
    root_etag = client.file_info('/').get_etag()
    test_etag = client.file_info('/test').get_etag()

    step(6, 'verify etag propagation')
    root_etag2 = client.file_info('/').get_etag()
    error_check(root_etag != root_etag2, 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag2))

    step(8, 'verify etag propagation')
    root_etag3 = client.file_info('/').get_etag()
    error_check(root_etag2 != root_etag3, 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag2, root_etag3))

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

    step(16, 'verify etag propagation')
    root_etag7 = client.file_info('/').get_etag()
    test_etag5 = client.file_info('/test').get_etag()
    error_check(root_etag6 == root_etag7, 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))
    error_check(test_etag4 == test_etag5, 'recipient 2 unshares reshare '
                'etag for /test previous [%s] new [%s]' % (test_etag4, test_etag5))

@add_worker
def recipient4(step):

    user = '%s%i' % (config.oc_account_name, 5)

    step (2, 'Create workdir')

    d = make_workdir()
    run_ocsync(d, user_num=5)

    client = get_oc_api()
    client.login(user, config.oc_account_password)

    step(4, 'get base etags to compare')
    root_etag = client.file_info('/').get_etag()
    sub_etag = client.file_info('/sub').get_etag()

    step(6, 'verify etag is NOT propagated')
    root_etag2 = client.file_info('/').get_etag()
    error_check(root_etag == root_etag2, 'owner uploads to /test/test2.txt '
                'etag for / previous [%s] new [%s]' % (root_etag, root_etag2))

    step(8, 'verify etag is NOT propagated')
    root_etag3 = client.file_info('/').get_etag()
    error_check(root_etag2 == root_etag3, 'recipient2 uploads to /test/test3.txt '
                'etag for / previous [%s] new [%s]' % (root_etag2, root_etag3))

    step(10, 'verify etag propagation')
    root_etag4 = client.file_info('/').get_etag()
    sub_etag2 = client.file_info('/sub').get_etag()
    error_check(root_etag3 != root_etag4, 'owner uploads to /test/sub/test4.txt '
                'etag for / previous [%s] new [%s]' % (root_etag3, root_etag4))
    error_check(sub_etag != sub_etag2, 'owner uploads to /test/sub/test4.txt '
                'etag for /sub previous [%s] new [%s]' % (sub_etag, sub_etag2))

    step(12, 'verify etag propagation')
    root_etag5 = client.file_info('/').get_etag()
    sub_etag3 = client.file_info('/sub').get_etag()
    error_check(root_etag4 != root_etag5, 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for / previous [%s] new [%s]' % (root_etag4, root_etag5))
    error_check(sub_etag2 != sub_etag3, 'recipient 1 uploads to /test/sub/test5.txt '
                'etag for /sub previous [%s] new [%s]' % (sub_etag2, sub_etag3))

    step(13, 'Upload to /sub')
    run_ocsync(d, user_num=5)
    createfile(os.path.join(d, 'sub', 'test6.txt'), '6', count=1000, bs=10)
    run_ocsync(d, user_num=5)

    step(14, 'verify etag propagation')
    root_etag6 = client.file_info('/').get_etag()
    sub_etag4 = client.file_info('/sub').get_etag()
    error_check(root_etag5 != root_etag6, 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for / previous [%s] new [%s]' % (root_etag5, root_etag6))
    error_check(sub_etag3 != sub_etag4, 'recipient 4 uploads to /sub/test6.txt through reshare '
                'etag for /sub previous [%s] new [%s]' % (sub_etag3, sub_etag4))

    step(16, 'verify etag propagation')
    root_etag7 = client.file_info('/').get_etag()
    error_check(root_etag6 != root_etag7, 'recipient 2 unshares reshare '
                'etag for / previous [%s] new [%s]' % (root_etag6, root_etag7))
    # /sub folder should be deleted at this point, so no checking

