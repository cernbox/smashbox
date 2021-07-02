from owncloud import HTTPResponseError

__doc__ = """

Test syncing when a directory turns into a file or back.

"""

from smashbox.utilities import *
from shutil import rmtree

def make_subdir(d, sub):
    return make_workdir(os.path.join(d, sub))

def expect_webdav_isfile(path, user_num=None):
    exitcode,stdout,stderr = runcmd('curl -s -k %s -XPROPFIND %s | xmllint --format -'%(config.get('curl_opts',''),oc_webdav_url(remote_folder=path, user_num=user_num)))
    error_check("NotFound" not in stdout, "Remote path %s does not exist" % path)
    error_check("d:collection" not in stdout, "Remote path %s is not a file" % path)

@add_worker
def dir_to_file(step):

    if compare_client_version('2.1.0', '<='):
        logger.warning('Skipping test, because the client version is known to behave incorrectly')
        return

    step(1, 'Create a folder and sync it')

    d = make_workdir()
    folder1 = make_subdir(d, 'folder1')
    folder2 = make_subdir(d, 'folder2')

    def make_folder(name):
        folder = make_subdir(folder1, name)
        sub_del = make_subdir(folder, 'sub_del')
        sub_move = make_subdir(folder, 'sub_move')
        createfile(os.path.join(folder, 'file-delete.txt'), '0', count=1000, bs=50)
        createfile(os.path.join(folder, 'file-move.txt'), '1', count=1000, bs=50)
        createfile(os.path.join(sub_del, 'file-sub-del.txt'), '2', count=1000, bs=50)
        createfile(os.path.join(sub_move, 'file-sub-move.txt'), '3', count=1000, bs=50)

    make_folder('dirtofile')
    make_folder('dirtofile2')

    # this will later replace dirtofile2
    createfile(os.path.join(folder1, 'dirtofile2-move'), '4', count=1000, bs=50)
    # and later this will become dirtofile2
    dirtofile2move = make_subdir(folder1, 'dirtofile2-move2')
    createfile(os.path.join(folder1, 'dirtofile2-move2', 'foo.txt'), '5', count=1000, bs=50)

    run_ocsync(folder1)
    # sanity check only
    expect_webdav_exist('dirtofile/file-delete.txt')
    expect_webdav_exist('dirtofile2/file-delete.txt')
    expect_webdav_exist('dirtofile2-move')

    # at this point, both client and server have 'dirtofile' folders


    step(2, 'Turn the folder into a file locally and propagate to the server')
    # This tests folder->file propagating to the server

    # we do this by syncing to a different folder, adjusting, syncing up again
    run_ocsync(folder2)
    mv(os.path.join(folder2, 'dirtofile', 'file-move.txt'), os.path.join(folder2, 'file-move.txt'))
    mv(os.path.join(folder2, 'dirtofile', 'sub_move'), os.path.join(folder2, 'sub_move'))
    rmtree(os.path.join(folder2, 'dirtofile'))
    createfile(os.path.join(folder2, 'dirtofile'), 'N', count=1000, bs=50)

    mv(os.path.join(folder2, 'dirtofile2', 'file-move.txt'), os.path.join(folder2, 'file-move2.txt'))
    mv(os.path.join(folder2, 'dirtofile2', 'sub_move'), os.path.join(folder2, 'sub_move2'))
    rmtree(os.path.join(folder2, 'dirtofile2'))
    mv(os.path.join(folder2, 'dirtofile2-move'), os.path.join(folder2, 'dirtofile2'))

    run_ocsync(folder2)

    error_check(os.path.isfile(os.path.join(folder2, 'dirtofile')), "expected 'dirtofile' to be a file")
    expect_webdav_isfile('dirtofile')
    expect_webdav_exist('file-move.txt')
    expect_webdav_exist('sub_move')
    error_check(os.path.isfile(os.path.join(folder2, 'dirtofile2')), "expected 'dirtofile2' to be a file")
    expect_webdav_isfile('dirtofile2')
    expect_webdav_exist('file-move2.txt')
    expect_webdav_exist('sub_move2')
    expect_webdav_does_not_exist('dirtofile2-move')


    step(3, 'Sync the folder that became a file into the old working tree')
    # This tests folder->file propagating from the server

    run_ocsync(folder1)

    # server is unchanged
    expect_webdav_isfile('dirtofile')
    expect_webdav_isfile('dirtofile2')

    # client has the files too
    expect_exists(os.path.join(folder1, 'dirtofile'))
    expect_exists(os.path.join(folder1, 'file-move.txt'))
    expect_exists(os.path.join(folder1, 'sub_move/file-sub-move.txt'))
    error_check(os.path.isfile(os.path.join(folder1, 'dirtofile')), "'dirtofile' didn't become a file")
    expect_exists(os.path.join(folder1, 'dirtofile2'))
    expect_exists(os.path.join(folder1, 'file-move2.txt'))
    expect_exists(os.path.join(folder1, 'sub_move2/file-sub-move.txt'))
    error_check(os.path.isfile(os.path.join(folder1, 'dirtofile2')), "'dirtofile2' didn't become a file")
    expect_does_not_exist(os.path.join(folder1, 'dirtofile2-move'))

    # at this point, both client and server have a 'dirtofile' file


    step(4, 'Turn the file into a folder locally and propagate to the server')
    # This tests file->folder propagating to the server

    # we do this by syncing to a different folder, adjusting, syncing up again
    run_ocsync(folder2)

    delete_file(os.path.join(folder2, 'dirtofile'))
    mkdir(os.path.join(folder2, 'dirtofile'))
    createfile(os.path.join(folder2, 'dirtofile', 'newfile.txt'), 'M', count=1000, bs=50)

    delete_file(os.path.join(folder2, 'dirtofile2'))
    mv(os.path.join(folder2, 'dirtofile2-move2'), os.path.join(folder2, 'dirtofile2'))

    run_ocsync(folder2)

    error_check(os.path.isdir(os.path.join(folder2, 'dirtofile')), "expected 'dirtofile' to be a folder")
    expect_webdav_exist('dirtofile/newfile.txt')
    error_check(os.path.isdir(os.path.join(folder2, 'dirtofile2')), "expected 'dirtofile2' to be a folder")
    expect_webdav_exist('dirtofile2/foo.txt')


    step(5, 'Sync the file that became a folder into the old working tree')
    # This tests file->folder propagating from the server

    run_ocsync(folder1)

    # server is unchanged
    expect_webdav_exist('dirtofile/newfile.txt')
    expect_webdav_exist('dirtofile2/foo.txt')

    # client has the file too, implying that dirtofile is a folder
    expect_exists(os.path.join(folder1, 'dirtofile/newfile.txt'))
    expect_exists(os.path.join(folder1, 'dirtofile2/foo.txt'))
