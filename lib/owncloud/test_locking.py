import re

from smashbox.owncloudorg.locking import *
from smashbox.utilities import *
import os
import signal

__doc__ = """

Test locking enforcement
+------+------------------------------------+
| Step |                User                |
+------+------------------------------------+
|    2 | Enable QA testing app              |
|    3 | Create dir/subdir/                 |
|    4 | Populate locks                     |
|    5 | Try to upload dir/subdir/file2.dat |
|    6 | Remove locks                       |
|    7 | Upload dir/subdir/file2.dat        |
+------+------------------------------------+

"""


DIR_NAME = 'dir'
SUBDIR_NAME = os.path.join(DIR_NAME, 'subdir')

testsets = [
    {
        'locks': [
            {
                'lock': LockProvider.LOCK_EXCLUSIVE,
                'path': DIR_NAME
            }
        ],
        'can_upload': False
    },
    {
        'locks': [
            {
                'lock': LockProvider.LOCK_SHARED,
                'path': DIR_NAME
            }
        ],
        'can_upload': True
    },
    {
        'locks': [
            {
                'lock': LockProvider.LOCK_EXCLUSIVE,
                'path': SUBDIR_NAME
            }
        ],
        'can_upload': False
    },
    {
        'locks': [
            {
                'lock': LockProvider.LOCK_SHARED,
                'path': SUBDIR_NAME
            }
        ],
        'can_upload': True
    },
    {
        'locks': [
            {
                'lock': LockProvider.LOCK_EXCLUSIVE,
                'path': DIR_NAME
            },
            {
                'lock': LockProvider.LOCK_SHARED,
                'path': SUBDIR_NAME
            }
        ],
        'can_upload': False
    },
    {
        'locks': [
            {
                'lock': LockProvider.LOCK_SHARED,
                'path': DIR_NAME
            },
            {
                'lock': LockProvider.LOCK_EXCLUSIVE,
                'path': SUBDIR_NAME
            }
        ],
        'can_upload': False
    },
    {
        'locks': [
            {
                'lock': LockProvider.LOCK_SHARED,
                'path': DIR_NAME
            },
            {
                'lock': LockProvider.LOCK_SHARED,
                'path': SUBDIR_NAME
            }
        ],
        'can_upload': True
    }
]

use_locks = config.get('locks', testsets[0]['locks'])
can_upload = config.get('can_upload', testsets[0]['can_upload'])
original_cmd = config.oc_sync_cmd


@add_worker
def owner_worker(step):

    if compare_client_version('2.1.1', '<='):
        # The client has a bug with permissions of folders on the first sync before 2.1.2
        logger.warning('Skipping test, because the client version is known to behave incorrectly')
        return

    if compare_oc_version('9.0', '<='):
        # The server has no fake locking support
        logger.warning('Skipping test, because the server has no fake locking support')
        return

    oc_api = get_oc_api()
    oc_api.login(config.oc_admin_user, config.oc_admin_password)
    lock_provider = LockProvider(oc_api)
    lock_provider.enable_testing_app()

    if not lock_provider.isUsingDBLocking():
        logger.warning('Skipping test, because DB Locking is not enabled or lock provisioning is not supported')
        return

    step(2, 'Create workdir')
    d = make_workdir()

    from owncloud import OCSResponseError
    try:
        lock_provider.unlock()
    except OCSResponseError:
        fatal_check(False, 'Testing App seems to not be enabled')

    step(3, 'Create test folder')

    mkdir(os.path.join(d, DIR_NAME))
    mkdir(os.path.join(d, SUBDIR_NAME))
    createfile(os.path.join(d, DIR_NAME, 'file.dat'), '0', count=1000, bs=1)
    createfile(os.path.join(d, SUBDIR_NAME, 'sub_file.dat'), '0', count=1000, bs=1)

    run_ocsync(d)

    step(4, 'Lock items')

    for lock in use_locks:
        fatal_check(
            lock_provider.is_locked(lock['lock'], config.oc_account_name, lock['path']) == False,
            'Resource is already locked'
        )

        lock_provider.lock(lock['lock'], config.oc_account_name, lock['path'])

        fatal_check(
            lock_provider.is_locked(lock['lock'], config.oc_account_name, lock['path']),
            'Resource should be locked'
        )

    step(5, 'Try to upload a file in locked item')

    createfile(os.path.join(d, SUBDIR_NAME, 'file2.dat'), '0', count=1000, bs=1)

    try:
        save_run_ocsync(d, seconds=10, max_sync_retries=1)
    except TimeoutError as err:
        if compare_client_version('2.1.0', '>='):
            # Max retries should terminate in time
            error_check(False, err.message)
        else:
            # Client does not terminate before 2.1: https://github.com/owncloud/client/issues/4037
            logger.warning(err.message)

    if can_upload:
        expect_webdav_exist(os.path.join(SUBDIR_NAME, 'file2.dat'))
    else:
        expect_webdav_does_not_exist(os.path.join(SUBDIR_NAME, 'file2.dat'))

    step(6, 'Unlock item and sync again')

    for lock in use_locks:
        fatal_check(
            lock_provider.is_locked(lock['lock'], config.oc_account_name, lock['path']),
            'Resource is already locked'
        )

        lock_provider.unlock(lock['lock'], config.oc_account_name, lock['path'])

        fatal_check(
            lock_provider.is_locked(lock['lock'], config.oc_account_name, lock['path']) == False,
            'Resource should be locked'
        )

    step(7, 'Upload a file in unlocked item')

    run_ocsync(d)

    expect_webdav_exist(os.path.join(SUBDIR_NAME, 'file2.dat'))

    step(8, 'Final - Unlock everything')

    lock_provider.unlock()
    lock_provider.disable_testing_app()


class TimeoutError(Exception):
    pass


def handler(signum, frame):
    config.oc_sync_cmd = original_cmd
    raise TimeoutError('Sync client did not terminate in time')


def save_run_ocsync(local_folder, seconds=10, max_sync_retries=1, remote_folder="", n=None, user_num=None):
    """
    A save variation of run_ocsync, that terminates after n seconds or x retries depending on the client version

    :param local_folder: The local folder to sync
    :param seconds: Number of seconds until the request should be terminated
    :param max_sync_retries: Number of retries for each sync
    :param remote_folder: The remote target folder to sync to
    :param n: Number of syncs
    :param user_num: User number
    """

    if compare_client_version('2.1.0', '>='):
        pattern = re.compile(r' \-\-max\-sync\-retries \d+')
        config.oc_sync_cmd = pattern.sub('', config.oc_sync_cmd)
        config.oc_sync_cmd += ' --max-sync-retries %i' % max_sync_retries

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)

    # This run_ocsync() may hang indefinitely
    run_ocsync(local_folder, remote_folder, n, user_num)

    signal.alarm(0)
    config.oc_sync_cmd = original_cmd
