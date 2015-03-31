
__doc__ = """

Test uploading a large number of files to a directory and then syncing

+-----------+-----------------------------------------------------+
|  Step     |  Uploader                                           |
|  Number   |                                                     |
+===========+=====================================================+
|  2        | Create work dir                                     |
+-----------+-----------------------------------------------------+
|  3        | Create directories and files on the server and      |
|           | then sync and validate on the client                |
+-----------+-----------------------------------------------------+
|  4        | final step                                          |
+-----------+-----------------------------------------------------+

Data Providers:

  test_sharePermissions:      Permissions to be applied to the share
  test_numFilesToCreate:      Number of files to create
  test_filesizeKB:            Size of file to create in KB
  dir_depth:                  How deep the directory structure should go
  style:                      Defines if the directory layout is flat or hierarchial
  num_file_rows:              How many rows in the file


"""

from smashbox.utilities import *
import glob
import re

filesizeKB = int(config.get('test_filesizeKB',10))
numFilesToCreate = config.get('test_numFilesToCreate', 10)
dir_depth = config.get ('dir_depth',5)
num_users = config.get ('oc_number_test_users', 3)
num_file_rows = config.get ('file_row_count', 100)
style = config.get ('dir_depth_style', 'flat')

testsets = [
    {
        'num_file_rows':1000,
        'num_users':10,
        'dir_depth':5,
        'test_numFilesToCreate':50,
        'test_filesizeKB':20,
        'style': 'flat',
    },
    {
        'num_file_rows':1000,
        'num_users':10,
        'dir_depth':5,
        'test_numFilesToCreate':50,
        'test_filesizeKB':200,
        'style': 'fluffy',
    },
    {
        'num_file_rows':1000,
        'num_users':10,
        'dir_depth':10,
        'test_numFilesToCreate':50,
        'test_filesizeKB':2000,
        'sytle': 'flat'
    },
    {
        'num_file_rows':1000,
        'num_users':10,
        'dir_depth':10,
        'test_numFilesToCreate':50,
        'test_filesizeKB':2000,
        'sytle': 'fluffy'
    },
]

@add_worker
def setup(step):

    step (1, 'Create test users')
    reset_owncloud_account(num_test_users=num_users)
    check_users(num_users)

    reset_rundir()
    reset_server_log_file()

    step (5, 'Validate server log file is clean')

    d = make_workdir()
    scrape_log_file(d)


def uploader (step):

    step (2,'Create workdir')
    d = make_workdir()
    uploader_num = int(re.search(r'\d+', d).group())

    step (3,'Create directories and files then sync and validate')

    filename = "%s%s" % (d,'/TEST_FILE_NEW_USER_SHARE.dat')
    createfile(filename,'0',count=1000,bs=filesizeKB)

    procName = reflection.getProcessName()

    if style is 'flat':
        for i in range(dir_depth):
            dir_name = "%s/%s_%d"%(procName, 'upload_dir', i)
            for j in range(1, numFilesToCreate):
                upload_name = "%s/%s_%d" % (dir_name, filename, j)
                webdav_upload(filename, upload_name)
    else:
        dir_name = procName
        for i in range(dir_depth):
            dir_name = "%s/%s_%d"%(dir_name, 'upload_dir', i)
            upload_dir = make_workdir(dir_name)
            for j in range(1, numFilesToCreate):
                filename = "%s%s%i%s" % (upload_dir,'/TEST_FILE_NEW_USER_SHARE_',j,'.dat')
                createfile(os.path.join(d,filename),'0',count=1000,bs=filesizeKB)

    run_ocsync(d,user_num=uploader_num)

    list_files(d, recursive=True)
    checkFilesExist(d) 

    step (4, 'Uploader final step')

for i in range(num_users):
    add_worker (uploader,name="uploader%02d"%(i+1))

def checkFilesExist (work_dir):

    logger.info ('Checking if files exist in local directory ')

    if style is 'flat':
        for i in range(dir_depth):
            dir_name = "%s/%s_%d"%(work_dir, 'upload_dir', i)
            for j in range(1, numFilesToCreate):
                filename = "%s%s%i%s" % (dir_name, '/TEST_FILE_NEW_USER_SHARE_',j,'.dat')
                full_name = os.path.join(work_dir, filename)
                logger.info ('Checking that %s is present ', full_name)
    else:
        dir_name = work_dir
        for i in range(dir_depth):
            dir_name = "%s/%s_%d"%(dir_name, 'upload_dir', i)
            for j in range(1, numFilesToCreate):
                filename = "%s%s%i%s" % (dir_name, '/TEST_FILE_NEW_USER_SHARE_',j,'.dat')
                full_name = os.path.join(work_dir, filename)
                logger.info ('Checking that %s is present ', full_name)


