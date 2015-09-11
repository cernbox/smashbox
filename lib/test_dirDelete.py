from smashbox.utilities import *

__doc__ = """ This test creates a deeply nested directory structure and then removes it

"""


import os.path
NESTING_LEVELS = config.get('dirDel_nestingLevels', 50)

nfiles = int(config.get('dirDel_nfiles', 100))

TEST_FILES = ['test%02d.dat'%i for i in range(nfiles)]

testsets = [
        { 'dirDel_nestingLevels': 50,
         'dirDel_nfiles': 100
        }
]
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
    
