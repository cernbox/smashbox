import os
import time
import tempfile


__doc__ = """ Check that changes to file are also propagated when file is moved
    
    +-----------+-----------------+------------------+
    |  Step     |  Client1        |  Client2         |
    +===========+======================+=============+
    |  2        | create ref file | create work dir  |
    |           | and workdir     |                  |
    +-----------+-----------------+------------------+
    |  3        | add files and   |                  |
    |           | sync            |                  |
    +-----------+-----------------+------------------+
    |  4        |                 | sync down        |
    |           |                 | and check        |
    +-----------+-----------------+------------------+
    |  5        | mod files and   |                  |
    |           | sync            |                  |
    +-----------+-----------------+------------------+
    |  6        |                 | sync down        |
    |           |                 | and check        |
    +-----------+-----------------+------------------+
    |  7        |                 | move files       |
    |           |                 | and modify       |
    +-----------+-----------------+------------------+
    |  8        | sync files and  |                  |
    |           | check           |                  |
    +-----------+-----------------+------------------+
    |  9        | check checksums | check checksums  |
    +-----------+-----------------+------------------+

    """

from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.utilities.monitoring import commit_to_monitoring

nfiles = int(config.get('deltamove_nfiles',10))
filesize = config.get('deltamove_filesize',1000)

if type(filesize) is type(''):
    filesize = eval(filesize)

# True => use new webdav endpoint (dav/files)
# False => use old webdav endpoint (webdav)
use_new_dav_endpoint = bool(config.get('use_new_dav_endpoint',True))

testsets = [
            { 'deltamove_filesize': OWNCLOUD_CHUNK_SIZE(0.01),
            'deltamove_nfiles':2,
            'use_new_dav_endpoint':True
            },
            { 'deltamove_filesize': OWNCLOUD_CHUNK_SIZE(3.5),
            'deltamove_nfiles':2,
            'use_new_dav_endpoint':True
            },
            
            ]

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
    d = make_workdir()

    # create the test file
    createfile(os.path.join(d,"TEST_FILE_MODIFIED.dat"),'0',count=1,bs=filesize)
    modify_file(os.path.join(d,"TEST_FILE_MODIFIED.dat"),'1',count=1,bs=1000)
    modify_file(os.path.join(d,"TEST_FILE_MODIFIED.dat"),'2',count=1,bs=1000)
    checksum_reference = md5sum(os.path.join(d,"TEST_FILE_MODIFIED.dat"))

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    k0 = count_files(d)
    
    step(3,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    logger.log(35,"Timestamp %f Files %d Size %d",time.time(),nfiles,filesize)

    for i in range(nfiles):
        createfile(os.path.join(d,"TEST_FILE_MODIFIED_%d.dat"%(i)),'0',count=1,bs=filesize)

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)
                   
    k1 = count_files(d)
                   
    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    step(5,"Modify files")

    for i in range(nfiles):
        modify_file(os.path.join(d,"TEST_FILE_MODIFIED_%d.dat"%(i)),'1',count=1,bs=1000)

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    k2 = count_files(d)
    
    error_check(k2-k0==nfiles,'Expecting to have %d files: see k2=%d k0=%d'%(nfiles,k2,k0))

    step(8,'Check moved and modified')

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    k3 = count_files(d)
    error_check(k3-k0==nfiles,'Expecting to have %d files: see k3=%d k0=%d'%(nfiles,k3,k0))

    step(9, "Final report")

    for i in range(nfiles):
        checksum = md5sum(os.path.join(d,"TEST_FILE_MODIFIED_MOVED_%d.dat"%(i)))
        error_check(checksum==checksum_reference,'Expecting to have equal checksums, got %s instead of %s'%(checksum,checksum_reference))
                          
    logger.info('SUCCESS: %d files found',k2)

@add_worker
def worker1(step):
    if finish_if_not_capable():
        return
    
    step(2,'Preparation')
    d = make_workdir()
    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)
    checksum_reference = md5sum(os.path.join(d,"TEST_FILE_MODIFIED.dat"))
    k0 = count_files(d)

    step(4,'Resync and check files added by worker0')

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    step(6,'Resync and check files modified by worker0')

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    k2 = count_files(d)

    error_check(k2-k0==nfiles,'Expecting to have %d files: see k2=%d k0=%d'%(nfiles,k2,k0))

    step(7,'Move and modify')

    for i in range(nfiles):
        mv(os.path.join(d,"TEST_FILE_MODIFIED_%d.dat"%(i)), os.path.join(d,"TEST_FILE_MODIFIED_MOVED_%d.dat"%(i)))

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    for i in range(nfiles):
        modify_file(os.path.join(d,"TEST_FILE_MODIFIED_MOVED_%d.dat"%(i)),'2',count=1,bs=1000)

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    k3 = count_files(d)

    error_check(k3-k0==nfiles,'Expecting to have %d files: see k3=%d k0=%d'%(nfiles,k3,k0))

    step(8,"Final report")
    for i in range(nfiles):
        checksum = md5sum(os.path.join(d,"TEST_FILE_MODIFIED_MOVED_%d.dat"%(i)))
        error_check(checksum==checksum_reference,'Expecting to have equal checksums, got %s instead of %s'%(checksum,checksum_reference))





