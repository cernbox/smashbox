
__doc__ = """

Test uploading a large number of files to a directory and then syncing

+--------+----------------------------------------------+-------------------------------------+
| Step   | Uploader                                     | Downloader                          |
| Number |                                              |                                     |
+========+==============================================+=====================================+
| 2      | Create work dir                              | Create work dir                     |
+--------+----------------------------------------------+-------------------------------------+
| 3      | Create directories and files and upload them |                                     |
+--------+----------------------------------------------+-------------------------------------+
| 4      | Validate files have been uploaded            |                                     |
+--------+----------------------------------------------+-------------------------------------+
| 5      |                                              | Sync                                |
+--------+----------------------------------------------+-------------------------------------+
| 6      |                                              | Validate files have been downloaded |
+--------+----------------------------------------------+-------------------------------------+

Data Providers:
  test_numFilesToCreate:      Number of files to create
  test_filesizeKB:            Size of file to create in KB
  dir_depth:                  How deep the directory structure should go
  dir_depth_style:            Defines if the directory layout is flat or hierarchial

"""

from smashbox.utilities import *
import re

filesizeKB = int(config.get('test_filesizeKB', 10))
numFilesToCreate = config.get('test_numFilesToCreate', 10)
dir_depth = config.get('dir_depth', 5)
style = config.get('dir_depth_style', 'nested')

testsets = [
    {
        'dir_depth': 5,
        'test_numFilesToCreate': 50,
        'test_filesizeKB': 20,
        'dir_depth_style': 'nested',
    },
    {
        'dir_depth': 5,
        'test_numFilesToCreate': 50,
        'test_filesizeKB': 200,
        'dir_depth_style': 'nested',
    },
    {
        'dir_depth': 10,
        'test_numFilesToCreate': 5,
        'test_filesizeKB': 2000,
        'dir_depth_style': 'flat'
    },
    {
        'dir_depth': 10,
        'test_numFilesToCreate': 5,
        'test_filesizeKB': 2000,
        'dir_depth_style': 'nested'
    },
]


def uploader(step):

    step(2, 'Create workdir')
    d = make_workdir()
    user_num = get_user_number_from_work_directory(d)

    step(3, 'Create directories and files then sync')
    files = []

    if style == 'flat':
        for i in range(dir_depth):
            dir_name = os.path.join(d, "%s_%d" % ('upload_dir', i))
            upload_dir = make_workdir(dir_name)
            for j in range(0, numFilesToCreate):
                upload_name = "%s_%d.dat" % ('TEST_FILE_NEW_USER_SHARE', j)
                createfile(os.path.join(upload_dir, upload_name), '0', count=1000, bs=filesizeKB)
                files.append(os.path.join(upload_dir, upload_name)[len(d) + 1:])
    else:
        dir_name = d
        for i in range(dir_depth):
            dir_name = os.path.join(dir_name, "%s_%d" % ('upload_dir', i))
            upload_dir = make_workdir(dir_name)
            for j in range(0, numFilesToCreate):
                upload_name = "%s_%d.dat" % ('TEST_FILE_NEW_USER_SHARE', j)
                createfile(os.path.join(upload_dir, upload_name), '0', count=1000, bs=filesizeKB)
                files.append(os.path.join(upload_dir, upload_name)[len(d) + 1:])

    run_ocsync(d, user_num=user_num)
    shared = reflection.getSharedObject()
    shared['FILES_%i' % user_num] = files

    step(4, 'Uploader verify files are uploaded')

    for f in files:
        expect_exists(os.path.join(d, f))
        expect_webdav_exist(f, user_num=user_num)

    step(5, 'Uploader final step')


def downloader(step):

    step(2, 'Create workdir')
    d = make_workdir()
    user_num = get_user_number_from_work_directory(d)

    step(5, 'Sync and validate')
    run_ocsync(d, user_num=user_num)

    step(6, 'Downloader validate that all files exist')
    shared = reflection.getSharedObject()
    files = shared['FILES_%i' % user_num]

    error_check(len(files) == dir_depth * numFilesToCreate, 'Number of files does not match')

    for f in files:
        expect_exists(os.path.join(d, f))

for u in range(config.oc_number_test_users):
    add_worker(uploader, name="uploader%02d" % (u+1))
    add_worker(downloader, name="downloader%02d" % (u+1))


def get_user_number_from_work_directory(work_dir):
    """
    :param work_dir: string Path of the directory
        /home/user/smashdir/test_uploadFiles-150522-111229/shareeTwo01
    :return: integer User number from the last directory name
    """

    work_dir = work_dir[len(config.rundir) + 1:]
    user_num = int(re.search(r'\d+', work_dir).group())
    return user_num
