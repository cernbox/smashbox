from smashbox.utilities import *

__doc__ = """ This test renames a directory A->B, creates an empty directory A and syncs. The move should be correctly propagated on the server.

Optionally the files are also moved back.

This pattern could happen in a situation when a sync client if switched off for some time.

This follows from discussion in: https://github.com/owncloud/client/issues/3324

TODO: a similar test for server side move.

"""

testsets = [ {'localDirRenameRecreate_DIRA':'DIRA', 
              'localDirRenameRecreate_DIRB':'DIRB',
              'localDirRenameRecreate_moveFilesBack':False},
             
             {'localDirRenameRecreate_DIRA':'DIRA', 
              'localDirRenameRecreate_DIRB':'DIRB',
              'localDirRenameRecreate_moveFilesBack':True}
             ]

import os.path

localDirRenameRecreate_DIRA = os.path.normpath(config.get('localDirRenameRecreate_DIRA','DIRA'))
localDirRenameRecreate_DIRB = os.path.normpath(config.get('localDirRenameRecreate_DIRB','DIRB'))

localDirRenameRecreate_nfiles = int(config.get('localDirRenameRecreate_nfiles',10))
localDirRenameRecreate_moveFilesBack = bool(config.get('localDirRenameRecreate_moveFilesBack',False))

TEST_FILES = ['test%02d.dat'%i for i in range(localDirRenameRecreate_nfiles)]

def check_files_exist(files,d):
    for fn in files:
        f = os.path.join(d,fn)
        logger.info("checking %s",f)
        error_check(os.path.isfile(f), "path %s should be a file"%f)    

@add_worker
def workerA(step):

    #cleanup remote and local test environment - this should be run once by one worker only
    reset_owncloud_account()
    reset_rundir()

    step(0,'create initial content and sync')

    # this will be our syncdir (this is different for every worker)
    syncdir = make_workdir()

    # create a folder and some files in it
    d1 = mkdir(os.path.join(syncdir,localDirRenameRecreate_DIRA))

    for f in TEST_FILES:
        fn = os.path.join(d1,f)
        createfile(fn,'0',count=1000,bs=1000)

    run_ocsync(syncdir)

    step(2,'move the files in the folder and sync')

    d2 = os.path.join(syncdir,localDirRenameRecreate_DIRB)

    mv(d1,d2)

    # recreate empty directory with the same name
    mkdir(d1)

    # optionally moves files back
    if localDirRenameRecreate_moveFilesBack:
        for f in TEST_FILES:
            fn = os.path.join(d2,f)
            mv(fn,d1)

    run_ocsync(syncdir)

    # check after runing our sync (workerA)
    check_final_state(syncdir)

    step(4,'check if nothing changed after running other sync (workerB)')

    check_final_state(syncdir)


@add_worker 
def workerB(step):

    step(1,'sync the initial content')

    syncdir = make_workdir()
    run_ocsync(syncdir)

    step(3,'sync again to check if the change is there')
    run_ocsync(syncdir)

    check_final_state(syncdir)
    

def check_final_state(syncdir):

    # we expect to find localDirRenameRecreate_DIRB and all test files in it
    # we expect localDirRenameRecreate_DIRA is deleted

    d1 = os.path.join(syncdir,localDirRenameRecreate_DIRA)
    d2 = os.path.join(syncdir,localDirRenameRecreate_DIRB)

    logger.info('checking %s',d1)
    error_check(os.path.isdir(d1), "path %s should be a directory"%d1)

    logger.info('checking %s',d2)
    error_check(os.path.isdir(d2), "path %s should be a directory"%d2)

    if localDirRenameRecreate_moveFilesBack:
        check_files_exist(TEST_FILES,d1)
    else:
        check_files_exist(TEST_FILES,d2)




    
    
