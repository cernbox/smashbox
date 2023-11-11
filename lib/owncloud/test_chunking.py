import os
import time
import tempfile


__doc__ = """ 
Upload a small file "small.dat" (10 kB)
Upload a big file "big.dat" (50 MB)
Overwrite big with small file, keeping the target name
Overwrite small with big file, keeping the target name
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

small_file_size = 10 # KB
big_file_size = 50000 # KB
zero_file_size = 0 # KB

# True => use new webdav endpoint (dav/files)
# False => use old webdav endpoint (webdav)
use_new_dav_endpoint = bool(config.get('use_new_dav_endpoint',True))

testsets = [
        {
          'use_new_dav_endpoint':True
        },
        {
          'use_new_dav_endpoint':False
        },
]

def expect_content(fn,md5):
    actual_md5 = md5sum(fn)
    error_check(actual_md5 == md5, "inconsistent md5 of %s: expected %s, got %s"%(fn,md5,actual_md5))

def finish_if_not_capable():
    # Finish the test if some of the prerequisites for this test are not satisfied
    if compare_oc_version('10.0', '<') and use_new_dav_endpoint == True:
        #Dont test for <= 9.1 with new endpoint, since it is not supported
        logger.warn("Skipping test since webdav endpoint is not capable for this server version")
        return True
    return False

@add_worker
def worker0(step):
    if finish_if_not_capable():
        return

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    shared = reflection.getSharedObject()
    d = make_workdir()
    run_ocsync(d)

    step(2,'Create and sync test files')

    createfile(os.path.join(d,'TEST_SMALL_TO_BIG.dat'),'0',count=1000,bs=small_file_size)
    createfile(os.path.join(d,'TEST_BIG_TO_SMALL.dat'),'0',count=1000,bs=big_file_size)
    #createfile(os.path.join(d,'TEST_ZERO_TO_BIG.dat'),'0',count=1000,bs=filesizeKB)
    #createfile(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'),'0',count=1000,bs=filesizeKB)

    shared['TEST_SMALL_TO_BIG'] = md5sum(os.path.join(d,'TEST_SMALL_TO_BIG.dat'))
    shared['TEST_BIG_TO_SMALL'] = md5sum(os.path.join(d,'TEST_BIG_TO_SMALL.dat'))
    logger.info('TEST_SMALL_TO_BIG: %s',shared['TEST_SMALL_TO_BIG'])
    logger.info('TEST_BIG_TO_SMALL: %s',shared['TEST_BIG_TO_SMALL'])

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    step(5,'Sync down and check if correct')

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)
    expect_content(os.path.join(d,'TEST_SMALL_TO_BIG.dat'), shared['TEST_SMALL_TO_BIG'])
    expect_content(os.path.join(d,'TEST_BIG_TO_SMALL.dat'), shared['TEST_BIG_TO_SMALL'])


@add_worker
def worker1(step):
    if finish_if_not_capable():
        return

    step(3,'Preparation')
    shared = reflection.getSharedObject()
    d = make_workdir()
    run_ocsync(d)

    expect_content(os.path.join(d,'TEST_SMALL_TO_BIG.dat'), shared['TEST_SMALL_TO_BIG'])
    expect_content(os.path.join(d,'TEST_BIG_TO_SMALL.dat'), shared['TEST_BIG_TO_SMALL'])

    step(4,'Ovverwrite files')

    createfile(os.path.join(d,'TEST_SMALL_TO_BIG.dat'),'1',count=1000,bs=big_file_size)
    createfile(os.path.join(d,'TEST_BIG_TO_SMALL.dat'),'1',count=1000,bs=small_file_size)
    shared['TEST_SMALL_TO_BIG'] = md5sum(os.path.join(d,'TEST_SMALL_TO_BIG.dat'))
    shared['TEST_BIG_TO_SMALL'] = md5sum(os.path.join(d,'TEST_BIG_TO_SMALL.dat'))
    logger.info('TEST_SMALL_TO_BIG: %s',shared['TEST_SMALL_TO_BIG'])
    logger.info('TEST_BIG_TO_SMALL: %s',shared['TEST_BIG_TO_SMALL'])

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    step(5,'Check if correct')
    expect_content(os.path.join(d,'TEST_SMALL_TO_BIG.dat'), shared['TEST_SMALL_TO_BIG'])
    expect_content(os.path.join(d,'TEST_BIG_TO_SMALL.dat'), shared['TEST_BIG_TO_SMALL'])

