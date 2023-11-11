import os
import requests
import random

__doc__ = """ Download a file and abort before the end of the transfer.
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

filesize = config.get('fileDownloadAbort_filesize', 900000000)
iterations = config.get('fileDownloadAbort_iterations', 25)

if type(filesize) is type(''):
    filesize = eval(filesize)

testsets = [
        { 'fileDownloadAbort_filesize': 900000000, 
          'fileDownloadAbort_iterations': 25
        }
]

@add_worker
def main(step):    

    step(1, 'Preparation')

    # cleanup server files from previous run
    reset_owncloud_account(num_test_users=1)
    check_users(1)

    # cleanup all local files for the test
    reset_rundir()

    d = make_workdir()
    run_ocsync(d,user_num=1)

    step(2, 'Add a file: filesize=%s'%filesize)

    create_hashfile(d,filemask='BLOB.DAT',size=filesize)
    list_files(d)
    run_ocsync(d,user_num=1)
    list_files(d)

    reset_server_log_file(True)

    step(3, 'Create link share')
    user1 = "%s%i"%(config.oc_account_name, 1)

    oc_api = get_oc_api()
    oc_api.login(user1, config.oc_account_password)

    share = oc_api.share_file_with_link('BLOB.DAT', perms=31)
    share_url = share.get_link() + '/download'

    # Start testing
    test_urls = [
        {
            'url': oc_public_webdav_url(),
            'auth': (share.get_token(), ''),
            'description': 'Public webdav URL'
        },
        {
            'url': share.get_link() + '/download',
            'auth': None,
            'description': 'Link share URL'
        },
        {
            'url': os.path.join(oc_webdav_url(), 'BLOB.DAT'),
            'auth': (user1, config.oc_account_password),
            'description': 'Webdav URL'
        },
    ]

    stepCount = 4

    for test_url in test_urls:
        cases = [
            {'use_range': False, 'abort': True, 'description': 'download abort'},
            {'use_range': True, 'abort': True, 'description': 'range download abort'},
            {'use_range': False, 'abort': False, 'description': 'full download'},
            {'use_range': True, 'abort': False, 'description': 'range download'},
        ]

        for case in cases:
            step(stepCount, test_url['description'] + ' ' + case['description']);
            for i in range(1, iterations):
                test_download(i, test_url['url'], test_url['auth'], case['use_range'], case['abort'])
            check_and_reset_logs()
            stepCount += 1

def check_and_reset_logs():
    d = make_workdir()
    scrape_log_file(d, True)
    reset_server_log_file(True)

    if len(reported_errors) > 0:
        raise AssertionError('Errors found in log, aborting')

def test_download(i, url, auth = None, use_range = False, abort = False):

    if use_range:
        range_start = random.randint(8192, filesize)
        range_end = random.randint(range_start, filesize - 8192)
    else:
        range_start = 0
        range_end = filesize

    if abort:
        break_bytes = random.randint(range_start + 8192, range_end - 8192)

    text = 'Download iteration %i' % i

    headers = {}
    if use_range:
        headers['Range'] = 'bytes=%i-%i' % (range_start, range_end)
        text += ' with range %s' % headers['Range']

    if abort:
        text += ' aborting after %i bytes' % break_bytes

    text += ' of total size %i ' % filesize

    text += ' url %s' % url

    logger.info(text)

    res = requests.get(url, auth=auth, stream=True, headers=headers)

    if use_range:
        expected_status_code = 206
    else:
        expected_status_code = 200

    error_check(res.status_code == expected_status_code, 'Could not download, status code %i' % res.status_code)

    read_bytes = 0;
    for chunk in res.iter_content(8192):
        read_bytes += len(chunk)
        if abort and read_bytes >= break_bytes:
            break

    res.close()

