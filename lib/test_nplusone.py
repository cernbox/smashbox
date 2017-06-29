import os
import time
import tempfile


__doc__ = """ Add nfiles to a directory and check consistency.
"""

from smashbox.utilities.hash_files import *
from smashbox.utilities.monitoring import push_to_monitoring
import platform
import logging

nfiles = int(config.get('nplusone_nfiles',20))
filesize = config.get('nplusone_filesize',10000)

# optional fs check before files are uploaded by worker0
fscheck = config.get('nplusone_fscheck',False)

logger = logging.getLogger()

ostype = platform.system() + platform.release()
logger.info(platform.system() + platform.release())

if type(filesize) is type(''):
    filesize = eval(filesize)

testsets = [
        { 'nplusone_filesize': 1000, 
          'nplusone_nfiles':100
        },

        { 'nplusone_filesize': OWNCLOUD_CHUNK_SIZE(0.3), 
          'nplusone_nfiles':10
        },

        { 'nplusone_filesize': OWNCLOUD_CHUNK_SIZE(1.3), 
          'nplusone_nfiles':2
        },

        { 'nplusone_filesize': OWNCLOUD_CHUNK_SIZE(3.5), 
          'nplusone_nfiles':1
        },

        { 'nplusone_filesize': (3.5,1.37), # standard file distribution: 10^(3.5) Bytes
          'nplusone_nfiles':10
        },

]

@add_worker
def worker0(step):    

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    total_size=0
    sizes=[]

    # compute the file sizes in the set
    for i in range(nfiles):
        size=size2nbytes(filesize)
        sizes.append(size)
        total_size+=size

    time0=time.time()

    logger.log(35,"Timestamp %f Files %d TotalSize %d",time.time(),nfiles,total_size)

    # create the test files
    for size in sizes:
        create_hashfile(d,size=size)

    if fscheck:
        # drop the caches (must be running as root on Linux)
        runcmd('echo 3 > /proc/sys/vm/drop_caches')
        
        ncorrupt = analyse_hashfiles(d)[2]
        fatal_check(ncorrupt==0, 'Corrupted files ON THE FILESYSTEM (%s) found'%ncorrupt)

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(d)[2]
    
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    logger.info('SUCCESS: %d files found',k1)

    step(4,"Final report")

    time1 = time.time()

    push_to_monitoring("cernbox.cboxsls.nplusone." + ostype + ".nfiles" + " " + str(nfiles))
    push_to_monitoring("cernbox.cboxsls.nplusone." + ostype + ".worker0.synced_files" + " " + str(k1 - k0))
    push_to_monitoring("cernbox.cboxsls.nplusone." + ostype + ".elapsed" + " " + str(time1-time0))
    push_to_monitoring("cernbox.cboxsls.nplusone." + ostype + ".transfer_rate" + " " + str(total_size/(time1-time0)))


@add_worker
def worker1(step):
    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)
    logger.info('SUCCESS: %d files found', k0)
    step(3,'Resync and check files added by worker0')

    run_ocsync(d)
    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

                       
    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(abs(k1-nfiles),k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%d) found'%ncorrupt) #Massimo 12-APR

    push_to_monitoring("cernbox.cboxsls.nplusone." + ostype + ".worker0.synced_files" + " " + str(k1 - k0))



