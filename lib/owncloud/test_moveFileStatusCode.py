from owncloud import HTTPResponseError

__doc__ = """

Test moving a file via webdav

"""

from smashbox.utilities import *

@add_worker
def move_non_existing_file(step):

    step(1, 'Create a folder and a file')
    d = make_workdir()
    dir_name = os.path.join(d, 'folder')
    local_dir = make_workdir(dir_name)

    createfile(os.path.join(d, 'file1.txt'), '0', count=1000, bs=50)
    createfile(os.path.join(local_dir, 'file3.txt'), '1', count=1000, bs=50)
    run_ocsync(d, user_num=1)

    expect_webdav_exist('file1.txt', user_num=1)
    expect_webdav_does_not_exist(os.path.join('folder', 'file2.txt'), user_num=1)
    expect_webdav_exist(os.path.join('folder', 'file3.txt'), user_num=1)

    step(2, 'Move the file into the folder')

    oc = get_oc_api()
    oc.login("%s%i" % (config.oc_account_name, 1), config.oc_account_password)

    try:
        oc.move('file1.txt', os.path.join('folder', 'file2.txt'))
    except HTTPResponseError as err:
        error_check(
            False,
            'Server replied with status code: %i' % err.status_code
        )

    expect_webdav_does_not_exist('file1.txt', user_num=1)
    expect_webdav_exist(os.path.join('folder', 'file2.txt'), user_num=1)
    expect_webdav_exist(os.path.join('folder', 'file3.txt'), user_num=1)

    step(3, 'Move non existing file into the folder')

    try:
        oc.move('file1.txt', os.path.join('folder', 'file2.txt'))
    except HTTPResponseError as err:
        error_check(
            err.status_code == 404,
            'Server replied with status code: %i' % err.status_code
        )

    expect_webdav_does_not_exist('file1.txt', user_num=1)
    expect_webdav_exist(os.path.join('folder', 'file2.txt'), user_num=1)
    expect_webdav_exist(os.path.join('folder', 'file3.txt'), user_num=1)
