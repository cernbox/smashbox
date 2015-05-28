from smashbox.utilities import *

__doc__ = """ This test moves a DIRA folder to DIRB folder.

By default, the top-level DIRA folder is moved to DIRB/DIRA
"""

# testsets = [ {'dirMove_DIRA':'DIRA', 
#               'dirMove_DIRB':'DIRB' },
# 
#              {'dirMove_DIRA':'A/A/A/DIRA', 
#               'dirMove_DIRB':'DIRB'},
# 
#              {'dirMove_DIRA':'DIRA',
#               'dirMove_DIRB':'B/B/B/DIRB'},
# 
#              {'dirMove_DIRA':'A/A/A/A/DIRA',
#               'dirMove_DIRB':'B/B/B/B/B/B/DIRB'}
#              ]

import os.path

NESTING_LEVELS = config.get('dirDel_nestingLevels', 50)

nfiles = int(config.get('dirDel_nfiles', 100))

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
    path = "0"
    for i in xrange(1, NESTING_LEVELS):
        path = path + "/" + str(i)
    d1 = mkdir(os.path.join(syncdir, path))

    for f in TEST_FILES:
        fn = os.path.join(d1,f)
        createfile(fn,'0',count=1,bs=1000)

    run_ocsync(syncdir)

    step(2,'delete the folder and sync')

    topLevelDir = path.split("/", 1)[0]
    d2 = os.path.join(syncdir, topLevelDir)

    remove_tree(d2)

    #createfile(os.path.join(syncdir,'touch'),'0',count=1,bs=1)

    expect_webdav_exist(topLevelDir)
    run_ocsync(syncdir)
    
    expect_does_not_exist(d2)
    expect_webdav_does_not_exist(topLevelDir)
    
# @add_worker 
# def workerB(step):
# 
#     step(1,'sync the initial content')
# 
#     syncdir = make_workdir()
#     run_ocsync(syncdir)
# 
#     step(3,'sync again to check if the change is there')
# 
#     run_ocsync(syncdir)
# 
#     # we expect to find DIRB and all test files in it
#     # we expect DIRA is deleted
# 
#     d1 = os.path.join(syncdir,DIRA)
#     d2 = os.path.join(syncdir,DIRB)
# 
#     logger.info('checking %s',d1)
#     error_check(not os.path.exists(d1), "path %s should not exist"%d1)
# 
#     logger.info('checking %s',d2)
#     error_check(os.path.isdir(d2), "path %s should be a directory"%d2)
# 
#     for fn in TEST_FILES:
#         f = os.path.join(d2,os.path.basename(d1),fn)
#         logger.info("checking %s",f)
#         error_check(os.path.isfile(f), "path %s should be a file"%f)

    
    
