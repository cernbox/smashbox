import os
import time
import tempfile


__doc__ = """ Add nfiles to a directory and check consistency.
    "excludetime" is information if to count preparation sync to the total sync time.
    Due to several engines being used, and possible running of other performance tests, 
    there is need for so called sync_directory d and count directory count_dir
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

nfiles = int(config.get('syncperf_nfiles',1))
filesize = config.get('syncperf_filesize',1000)
excludetime = True

if type(filesize) is type(''):
    filesize = eval(filesize)
    
testsets = [
        { 'syncperf_filesize': 1000, 
          'syncperf_nfiles':1,
        },
        { 'syncperf_filesize': 5000000, 
          'syncperf_nfiles':1,
        },
        { 'syncperf_filesize': 500000000, 
          'syncperf_nfiles':1,
        },
]

@add_worker
def worker0(step): 
    step(1,'Preparation')
    d = make_workdir()
    array = prepare_workdir(d)
    count_dir = array[0]
    d = array[1]
    step(2,'Pre-sync')
    run_ocsync(d,option=exclude_time)
    
    k0 = count_files(count_dir)

    step(4,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    for i in range(nfiles):
        create_hashfile(count_dir,size=filesize)

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(count_dir)[2]
    
    k1 = count_files(count_dir)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    logger.info('SUCCESS: %d files found',k1)
        
@add_worker
def worker1(step):
    step(2,'Preparation')
    d = make_workdir()
    array = get_workdir(d)
    count_dir = array[0]
    d = array[1]
    step(3,'Pre-sync')
    run_ocsync(d,option=exclude_time)
    k0 = count_files(count_dir)

    step(5,'Resync and check files added by worker0')

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(count_dir)[2]
    k1 = count_files(count_dir)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)
    
def prepare_workdir(d):
    cdir = os.path.join(d,"0")
    remove_tree(cdir)
    reset_owncloud_account()
    mkdir(cdir)
    d = cdir
    return [cdir,d]

def get_workdir(d):
    cdir = os.path.join(d,"0")
    remove_tree(cdir)  
    mkdir(cdir)
    d = cdir  
    return [cdir,d]

def eval_excudetime(excludetime):
    if excludetime:   
        return "exclude_time"
    else:
        return None

