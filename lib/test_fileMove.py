from smashbox.utilities import *

__doc__ = """ This test moves files from one folder to another.

"""

testsets = [ {'dirMove_DIRA':'DIRA', 
              'dirMove_DIRB':'DIRB' }
             ]

import os.path

DIRA = os.path.normpath(config.get('dirMove_DIRA','DIRA'))
DIRB = os.path.normpath(config.get('dirMove_DIRB','DIRB'))

nfiles = int(config.get('dirMove_nfiles',10))

TEST_FILES = ['test%02d.dat'%i for i in range(nfiles)]

@add_worker
def workerA(step):

    #cleanup remote and local test environment - this should be run once by one worker only
    reset_owncloud_account()
    reset_rundir()

    step(0,'create initial content and sync')

    # this will be our syncdir (this is different for every worker)
    syncdir = make_workdir()

    # create a folder and some files in it
    d1 = mkdir(os.path.join(syncdir,DIRA))

    for f in TEST_FILES:
        fn = os.path.join(d1,f)
        createfile(fn,'0',count=1000,bs=1000)

    run_ocsync(syncdir)

    step(2,'move the folder and sync')

    d2 = mkdir(os.path.join(syncdir,DIRB))

    mkdir(d2)

    for f in TEST_FILES:
        fn = os.path.join(d1,f)
        mv(fn,d2)

    #createfile(os.path.join(syncdir,'touch'),'0',count=1,bs=1)

    run_ocsync(syncdir)
    
@add_worker 
def workerB(step):

    step(1,'sync the initial content')

    syncdir = make_workdir()
    run_ocsync(syncdir)

    step(3,'sync again to check if the change is there')

    run_ocsync(syncdir)

    # we expect to find DIRB and all test files in it
    # we expect DIRA is deleted

    d1 = os.path.join(syncdir,DIRA)
    d2 = os.path.join(syncdir,DIRB)

    logger.info('checking %s',d1)
    error_check(os.path.exists(d1), "path %s should exist"%d1)

    logger.info('checking %s',d2)
    error_check(os.path.isdir(d2), "path %s should be a directory"%d2)

    for fn in TEST_FILES:
        f = os.path.join(d2,fn)
        logger.info("checking %s",f)
        error_check(os.path.isfile(f), "path %s should be a file"%f)

    
    
