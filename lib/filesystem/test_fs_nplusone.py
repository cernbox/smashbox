import os
import time
import tempfile


__doc__ = """ Add nfiles to a directory and check consistency.
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

nfiles = int(config.get('fs_nplusone_nfiles',10))
filesize = config.get('fs_nplusone_filesize',1000)
fspath0 = config.get('fs_nplusone_fspath0',"")
fspath1 = config.get('fs_nplusone_fspath1',"")
conf = config['oc_server_folder']

if type(filesize) is type(''):
    filesize = eval(filesize)

testsets = [
        { 'fs_nplusone_filesize': 1000, 
          'fs_nplusone_nfiles':100
        },

        { 'fs_nplusone_filesize': OWNCLOUD_CHUNK_SIZE(0.3), 
          'fs_nplusone_nfiles':10
        },

        { 'fs_nplusone_filesize': OWNCLOUD_CHUNK_SIZE(1.3), 
          'fs_nplusone_nfiles':2
        },

        { 'fs_nplusone_filesize': OWNCLOUD_CHUNK_SIZE(3.5), 
          'fs_nplusone_nfiles':1
        },

        { 'fs_nplusone_filesize': (3.5,1.37), # standard file distribution: 10^(3.5) Bytes
          'fs_nplusone_nfiles':10
        },

]

@add_worker
def worker0(step):    

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    
    if fspath0:
        d = os.path.join(fspath0,conf)
    else:
        d = make_workdir()
        run_ocsync(d)
    
    k0 = count_files(d)

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    for i in range(nfiles):
        logger.info('file number {}'.format(i+1)) 
        create_hashfile(d,size=filesize)

    if fspath0:
        d = os.path.join(fspath0,conf)
        
    else:
        run_ocsync(d)
        
    ncorrupt = analyse_hashfiles(d)[2]
    
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    logger.info('SUCCESS: %d files found',k1)
        
@add_worker
def worker1(step):
    step(1,'Preparation')

    if fspath1:
        d = os.path.join(fspath1,conf)

    else:
        d = make_workdir() 
        run_ocsync(d) 


    k0 = count_files(d)

    step(3,'Resync and check files added by worker0')

    if (fspath1 and fspath0):
        d = os.path.join(fspath1,conf)

    else:
        run_ocsync(d)


    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)




