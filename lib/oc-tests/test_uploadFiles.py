
__doc__ = """

Test uploading a large number of files to a directory and then syncing

+-----------+----------------------+------------------+----------------------------+
|  Step     |  Sharer              |  Sharee One      |  Sharee Two                |
|  Number   |                      |                  |                            |
+===========+======================+==================+============================|
|  2        | create work dir      | create work dir  |  create work dir           |
+-----------+----------------------+------------------+----------------------------+
|  3        | Create test dir      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  4        | Shares test dir with |                  |                            |
|           | Sharee One and Two   |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  5        |                      | Syncs shared dir | syncs Shared dir           |
+-----------+----------------------+------------------+----------------------------+
|  6        |                      | creates new      |                            |
|           |                      | files and syncs  |                            |
+-----------+----------------------+------------------+----------------------------+
|  7        | syncs and validates  |                  |  syncs and validates       |
|           | new files exist      |                  |  new files exist           |
+-----------+----------------------+------------------+----------------------------+
|  8        | final step           | final step       |  final step                |
+-----------+----------------------+------------------+----------------------------+

Data Providers:

  test_sharePermissions:      Permissions to be applied to the share
  test_numFilesToCreate:      Number of files to create
  test_filesizeKB:            Size of file to create in KB


"""

from smashbox.utilities import *
import glob

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

filesizeKB = int(config.get('test_filesizeKB',10))
sharePermissions = config.get('test_sharePermissions', OCS_PERMISSION_ALL)
numFilesToCreate = config.get('test_numFilesToCreate', 1)

testsets = [
    {
        'test_sharePermissions':OCS_PERMISSION_ALL,
        'test_numFilesToCreate':50,
        'test_filesizeKB':20000
    },
    {
        'test_sharePermissions':OCS_PERMISSION_ALL,
        'test_numFilesToCreate':500,
        'test_filesizeKB':2000
    },
    {
        'test_sharePermissions':OCS_PERMISSION_READ | OCS_PERMISSION_CREATE | OCS_PERMISSION_UPDATE,
        'test_numFilesToCreate':50,
        'test_filesizeKB':20000
    },
]

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account(num_test_users=config.oc_number_test_users)
    check_users(config.oc_number_test_users)

    reset_rundir()
    reset_server_log_file()

    step (15, 'Validate server log file is clean')

    d = make_workdir()
    scrape_log_file(d)


@add_worker
def sharer(step):

    step (2,'Create workdir')
    d = make_workdir()

    step (3,'Create initial test directory')

    procName = reflection.getProcessName()
    dirName = "%s/%s"%(procName, 'localShareDir')
    localDir = make_workdir(dirName)

    list_files(d)
    run_ocsync(d,user_num=1)
    list_files(d)

    step (4,'Sharer shares directory')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)

    shared = reflection.getSharedObject()

    kwargs = {'perms': sharePermissions}
    shared['SHARE_LOCAL_DIR_U2'] = share_file_with_user ('localShareDir', user1, user2, **kwargs)
    shared['SHARE_LOCAL_DIR_U3'] = share_file_with_user ('localShareDir', user1, user3, **kwargs)

    step (7, 'Sharer validates newly added files')

    run_ocsync(d,user_num=1)

    list_files(d+'/localShareDir')
    checkFilesExist(d) 

    step (8, 'Sharer final step')

@add_worker
def shareeOne(step):

    step (2, 'Sharee One creates workdir')
    d = make_workdir()

    step (5,'Sharee One syncs and validates directory exist')

    run_ocsync(d,user_num=2)
    list_files(d)

    sharedDir = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedDir)
    error_check(os.path.exists(sharedDir), "Directory %s should exist" %sharedDir)

    step (6, 'Sharee One creates files')

    logger.info ('ShareeOne is creating %i files', numFilesToCreate)
    if numFilesToCreate == 1:
      createfile(os.path.join(d,'localShareDir/TEST_FILE_NEW_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    else:
      for i in range(1, numFilesToCreate):
        filename = "%s%i%s" % ('localShareDir/TEST_FILE_NEW_USER_SHARE_',i,'.dat')
        createfile(os.path.join(d,filename),'0',count=1000,bs=filesizeKB)

    run_ocsync(d,user_num=2)

    list_files(d+'/localShareDir')
    checkFilesExist(d) 

    step (8, 'Sharee One final step')

@add_worker
def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    procName = reflection.getProcessName()
    dirName = "%s/%s"%(procName, 'localShareDir')
    localDir = make_workdir(dirName)

    step (5, 'Sharee two syncs and validates directory exists')

    run_ocsync(d,user_num=3)
    list_files(d)

    sharedDir = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedDir)
    error_check(os.path.exists(sharedDir), "Directory %s should exist" %sharedDir)

    step (7, 'Sharee two validates new files exist')

    run_ocsync(d,user_num=3)

    list_files(d+'/localShareDir')
    checkFilesExist(d) 

    step (8, 'Sharee Two final step')

def checkFilesExist (tmpDir):

    logger.info ('Checking if files exist in local directory ')

    if numFilesToCreate == 1:
      sharedFile = os.path.join(tmpDir,'localShareDir/TEST_FILE_NEW_USER_SHARE.dat')
      logger.info ('Checking that %s is present in local directory ', sharedFile)
      error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)
    else:
      for i in range(1,numFilesToCreate):
        filename = "%s%i%s" % ('localShareDir/TEST_FILE_NEW_USER_SHARE_',i,'.dat')
        logger.info ('Checking that %s is present in local directory ', filename)
        sharedFile = os.path.join(tmpDir, filename)
        error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

