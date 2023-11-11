from smashbox.utilities import *

__doc__ = """

Test basic file sharing by link

Covers:
 * Single file share: https://github.com/owncloud/core/pull/19619
 * Folder share, single file direct download (click on file list)
 * Folder share, select single file and download (checkbox)
 * Folder share, select multiple files and download (checkbox)
 * Folder share, download full folder

"""


filesize_kb = int(config.get('share_filesizeKB', 10))

test_downloader = config.get('test_downloader', 'full_folder')

testsets = [
    {
        'test_downloader': 'single_file'
    },
    {
        'test_downloader': 'direct_single_files'
    },
    {
        'test_downloader': 'selected_single_files'
    },
    {
        'test_downloader': 'full_folder'
    },
    {
        'test_downloader': 'full_subfolder'
    },
    {
        'test_downloader': 'selected_files'
    }
]


@add_worker
def setup(step):

    step(1, 'create test users')
    reset_owncloud_account(num_test_users=2)
    check_users(2)

    reset_rundir()
    reset_server_log_file()

    step(6, 'Validate server log file is clean')

    d = make_workdir()
    scrape_log_file(d)


@add_worker
def sharer(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(3, 'Create initial test files and directories')

    proc_name = reflection.getProcessName()
    dir_name = os.path.join(proc_name, 'localShareDir')
    local_dir = make_workdir(dir_name)
    subdir_dir = make_workdir(os.path.join(dir_name, 'subdir'))

    createfile(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE1.txt'), '1', count=1000, bs=filesize_kb)
    createfile(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE2.txt'), '2', count=1000, bs=filesize_kb)
    createfile(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE3.txt'), '3', count=1000, bs=filesize_kb)
    createfile(os.path.join(subdir_dir, 'TEST_FILE_LINK_SHARE4.txt'), '4', count=1000, bs=filesize_kb)
    createfile(os.path.join(subdir_dir, 'TEST_FILE_LINK_SHARE5.txt'), '5', count=1000, bs=filesize_kb)
    createfile(os.path.join(subdir_dir, 'TEST_FILE_LINK_SHARE6.txt'), '6', count=1000, bs=filesize_kb)
    shared = reflection.getSharedObject()
    shared['MD5_TEST_FILE_LINK_SHARE1'] = md5sum(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE1.txt'))
    shared['MD5_TEST_FILE_LINK_SHARE2'] = md5sum(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE2.txt'))
    shared['MD5_TEST_FILE_LINK_SHARE3'] = md5sum(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE3.txt'))
    shared['MD5_TEST_FILE_LINK_SHARE4'] = md5sum(os.path.join(subdir_dir, 'TEST_FILE_LINK_SHARE4.txt'))
    shared['MD5_TEST_FILE_LINK_SHARE5'] = md5sum(os.path.join(subdir_dir, 'TEST_FILE_LINK_SHARE5.txt'))
    shared['MD5_TEST_FILE_LINK_SHARE6'] = md5sum(os.path.join(subdir_dir, 'TEST_FILE_LINK_SHARE6.txt'))

    list_files(d)
    run_ocsync(d, user_num=1)
    list_files(d)

    step(4, 'Sharer shares file as link')

    oc_api = get_oc_api()
    oc_api.login("%s%i" % (config.oc_account_name, 1), config.oc_account_password)

    kwargs = {'perms': 31}
    share = oc_api.share_file_with_link(os.path.join('localShareDir', 'TEST_FILE_LINK_SHARE1.txt'), **kwargs)
    shared['SHARE_LINK_TOKEN_TEST_FILE_LINK_SHARE1'] = share.token
    share = oc_api.share_file_with_link('localShareDir', **kwargs)
    shared['SHARE_LINK_TOKEN_TEST_DIR'] = share.token


def public_downloader_single_file(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(5, 'Downloads and validate')

    shared = reflection.getSharedObject()
    url = oc_webdav_url(
        remote_folder=os.path.join('index.php', 's', shared['SHARE_LINK_TOKEN_TEST_FILE_LINK_SHARE1'], 'download'),
        webdav_endpoint=config.oc_root
    )

    download_target = os.path.join(d, 'TEST_FILE_LINK_SHARE1.txt')
    runcmd('curl -k %s -o \'%s\' \'%s\'' % (config.get('curl_opts', ''), download_target, url))
    expect_not_modified(download_target, shared['MD5_TEST_FILE_LINK_SHARE1'])


def public_downloader_direct_single_files(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(5, 'Downloads and validate')

    shared = reflection.getSharedObject()
    url = oc_webdav_url(
        remote_folder=os.path.join(
            'index.php', 's',
            shared['SHARE_LINK_TOKEN_TEST_DIR'],
            'download?path=%2F&files=TEST_FILE_LINK_SHARE1.txt'
        ),
        webdav_endpoint=config.oc_root
    )

    download_target = os.path.join(d, 'TEST_FILE_LINK_SHARE1.txt')
    runcmd('curl -k %s -o \'%s\' \'%s\'' % (config.get('curl_opts', ''), download_target, url))
    expect_not_modified(download_target, shared['MD5_TEST_FILE_LINK_SHARE1'])


def public_downloader_selected_single_files(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(5, 'Downloads and validate')

    shared = reflection.getSharedObject()

    if compare_oc_version('10.0', '<'):
        url = oc_webdav_url(
            remote_folder=os.path.join(
                'index.php', 's',
                shared['SHARE_LINK_TOKEN_TEST_DIR'],
                'download?path=%2F&files=%5B%22TEST_FILE_LINK_SHARE1.txt%22%5D'
            ),
            webdav_endpoint=config.oc_root
        )
    else:
        # Api changed in 10.0
        # http://localhost/owncloudtest/index.php/s/Q3ZMB4S8xveM2x5/download?path=%2F&files[]=TEST_FILE_LINK_SHARE1.txt&files[]=TEST_FILE_LINK_SHARE2.txt
        url = oc_webdav_url(
            remote_folder=os.path.join(
                'index.php', 's',
                shared['SHARE_LINK_TOKEN_TEST_DIR'],
                'download?path=%2F&files%5B%5D=TEST_FILE_LINK_SHARE1.txt'
            ),
            webdav_endpoint=config.oc_root
        )

    download_target = os.path.join(d, 'TEST_FILE_LINK_SHARE1.txt')
    runcmd('curl -k %s -o \'%s\' \'%s\'' % (config.get('curl_opts', ''), download_target, url))
    expect_not_modified(download_target, shared['MD5_TEST_FILE_LINK_SHARE1'])


def public_downloader_full_folder(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(5, 'Downloads and validate')

    shared = reflection.getSharedObject()
    url = oc_webdav_url(
        remote_folder=os.path.join('index.php', 's', shared['SHARE_LINK_TOKEN_TEST_DIR'], 'download'),
        webdav_endpoint=config.oc_root
    )

    download_target = os.path.join(d, '%s%s' % (shared['SHARE_LINK_TOKEN_TEST_DIR'], '.zip'))
    unzip_target = os.path.join(d, 'unzip')
    runcmd('curl -v -k %s -o \'%s\' \'%s\'' % (config.get('curl_opts', ''), download_target, url))
    runcmd('unzip -d %s %s' % (unzip_target, download_target))

    list_files(d, recursive=True)

    expect_exists(os.path.join(unzip_target, 'localShareDir'))
    expect_exists(os.path.join(unzip_target, 'localShareDir', 'TEST_FILE_LINK_SHARE1.txt'))
    expect_exists(os.path.join(unzip_target, 'localShareDir', 'TEST_FILE_LINK_SHARE2.txt'))
    expect_exists(os.path.join(unzip_target, 'localShareDir', 'TEST_FILE_LINK_SHARE3.txt'))
    expect_exists(os.path.join(unzip_target, 'localShareDir', 'subdir'))
    expect_exists(os.path.join(unzip_target, 'localShareDir', 'subdir', 'TEST_FILE_LINK_SHARE4.txt'))
    expect_exists(os.path.join(unzip_target, 'localShareDir', 'subdir', 'TEST_FILE_LINK_SHARE5.txt'))
    expect_exists(os.path.join(unzip_target, 'localShareDir', 'subdir', 'TEST_FILE_LINK_SHARE6.txt'))

    expect_not_modified(
        os.path.join(unzip_target, 'localShareDir', 'TEST_FILE_LINK_SHARE1.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE1']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'localShareDir', 'TEST_FILE_LINK_SHARE2.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE2']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'localShareDir', 'TEST_FILE_LINK_SHARE3.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE3']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'localShareDir', 'subdir', 'TEST_FILE_LINK_SHARE4.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE4']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'localShareDir', 'subdir', 'TEST_FILE_LINK_SHARE5.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE5']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'localShareDir', 'subdir', 'TEST_FILE_LINK_SHARE6.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE6']
    )


def public_downloader_full_subfolder(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(5, 'Downloads and validate')

    shared = reflection.getSharedObject()
    url = oc_webdav_url(
        remote_folder=os.path.join(
            'index.php',
            's',
            shared['SHARE_LINK_TOKEN_TEST_DIR'],
            'download?path=%2F&files=subdir'
        ),
        webdav_endpoint=config.oc_root
    )

    download_target = os.path.join(d, '%s%s' % (shared['SHARE_LINK_TOKEN_TEST_DIR'], '.zip'))
    unzip_target = os.path.join(d, 'unzip')
    runcmd('curl -v -k %s -o \'%s\' \'%s\'' % (config.get('curl_opts', ''), download_target, url))
    runcmd('unzip -d %s %s' % (unzip_target, download_target))

    list_files(d, recursive=True)

    expect_exists(os.path.join(unzip_target, 'subdir'))
    expect_exists(os.path.join(unzip_target, 'subdir', 'TEST_FILE_LINK_SHARE4.txt'))
    expect_exists(os.path.join(unzip_target, 'subdir', 'TEST_FILE_LINK_SHARE5.txt'))
    expect_exists(os.path.join(unzip_target, 'subdir', 'TEST_FILE_LINK_SHARE6.txt'))

    expect_not_modified(
        os.path.join(unzip_target, 'subdir', 'TEST_FILE_LINK_SHARE4.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE4']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'subdir', 'TEST_FILE_LINK_SHARE5.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE5']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'subdir', 'TEST_FILE_LINK_SHARE6.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE6']
    )


def public_downloader_selected_files(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(5, 'Downloads and validate')

    shared = reflection.getSharedObject()


    if compare_oc_version('10.0', '<'):
        url = oc_webdav_url(
            remote_folder=os.path.join(
                'index.php', 's',
                shared['SHARE_LINK_TOKEN_TEST_DIR'],
                'download?path=%2F&files=%5B%22TEST_FILE_LINK_SHARE1.txt%22%2C%22TEST_FILE_LINK_SHARE2.txt%22%5D'
            ),
            webdav_endpoint=config.oc_root
        )
    else:
        # Api changed in 10.0
        # http://localhost/owncloudtest/index.php/s/Q3ZMB4S8xveM2x5/download?path=%2F&files[]=TEST_FILE_LINK_SHARE1.txt&files[]=TEST_FILE_LINK_SHARE2.txt
        url = oc_webdav_url(
            remote_folder=os.path.join(
                'index.php', 's',
                shared['SHARE_LINK_TOKEN_TEST_DIR'],
                'download?path=%2F&files%5B%5D=TEST_FILE_LINK_SHARE1.txt&files%5B%5D=TEST_FILE_LINK_SHARE2.txt'
            ),
            webdav_endpoint=config.oc_root
        )

    download_target = os.path.join(d, '%s%s' % (shared['SHARE_LINK_TOKEN_TEST_DIR'], '.zip'))
    unzip_target = os.path.join(d, 'unzip')
    runcmd('curl -v -k %s -o \'%s\' \'%s\'' % (config.get('curl_opts', ''), download_target, url))
    runcmd('unzip -d %s %s' % (unzip_target, download_target))

    list_files(d, recursive=True)

    expect_does_not_exist(os.path.join(unzip_target, 'localShareDir'))
    expect_exists(os.path.join(unzip_target, 'TEST_FILE_LINK_SHARE1.txt'))
    expect_exists(os.path.join(unzip_target, 'TEST_FILE_LINK_SHARE2.txt'))
    expect_does_not_exist(os.path.join(unzip_target, 'TEST_FILE_LINK_SHARE3.txt'))

    expect_not_modified(
        os.path.join(unzip_target, 'TEST_FILE_LINK_SHARE1.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE1']
    )
    expect_not_modified(
        os.path.join(unzip_target, 'TEST_FILE_LINK_SHARE2.txt'),
        shared['MD5_TEST_FILE_LINK_SHARE2']
    )


if test_downloader == 'single_file':
    add_worker(public_downloader_single_file, name=test_downloader)
elif test_downloader == 'direct_single_files':
    add_worker(public_downloader_direct_single_files, name=test_downloader)
elif test_downloader == 'selected_single_files':
    add_worker(public_downloader_selected_single_files, name=test_downloader)
elif test_downloader == 'full_folder':
    add_worker(public_downloader_full_folder, name=test_downloader)
elif test_downloader == 'full_subfolder':
    add_worker(public_downloader_full_subfolder, name=test_downloader)
elif test_downloader == 'selected_files':
    add_worker(public_downloader_selected_files, name=test_downloader)
