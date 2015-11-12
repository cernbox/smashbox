import os
import time
import tempfile


__doc__ = """ Add nfiles to a directory and check consistency.

    "syncperf_fullsyncdir" is defined as (number of directories) / (number of files) / (size of files) 
        - if not in the correct format, it will execute with empty directory.
    
    "excludetime" is information if to count preparation sync to the total sync time.
    
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

nfiles = int(config.get('syncperf_nfiles',10))
filesize = config.get('syncperf_filesize',1000)
excludetime = config.get('syncperf_excludetime',True)
fullsyncdir = config.get('syncperf_fullsyncdir',False)

if type(filesize) is type(''):
    filesize = eval(filesize)
full_dir_size = "10/100/10000"
testsets = [
        { 'syncperf_filesize': 1000, 
          'syncperf_nfiles':1,
          'syncperf_fullsyncdir':None,
          'syncperf_excludetime':True
        },
        { 'syncperf_filesize': 5000000, 
          'syncperf_nfiles':1,
          'syncperf_fullsyncdir':None,
          'syncperf_excludetime':True
        },
        { 'syncperf_filesize': 500000000, 
          'syncperf_nfiles':1,
          'syncperf_fullsyncdir':None,
          'syncperf_excludetime':True
        },
        { 'syncperf_filesize': 1000, 
          'syncperf_nfiles':1,
          'syncperf_fullsyncdir':full_dir_size,
          'syncperf_excludetime':True
        },
        { 'syncperf_filesize': 5000000, 
          'syncperf_nfiles':1,
          'syncperf_fullsyncdir':full_dir_size,
          'syncperf_excludetime':True
        },
        { 'syncperf_filesize': 500000000, 
          'syncperf_nfiles':1,
          'syncperf_fullsyncdir':full_dir_size,
          'syncperf_excludetime':True
        },
]

@add_worker
def worker0(step): 
    
    exclude_time = eval_excudetime(excludetime)
    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()
    
    step(1,'Preparation')
    d = make_workdir()
    count_dir = prepare_workdir(d)
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
    exclude_time = eval_excudetime(excludetime)
    step(1,'Preparation')
    d = make_workdir()
    count_dir = get_workdir(d)
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
    cdir = d
    if fullsyncdir!=None:
        conf = fullsyncdir.split('/')
        if len(conf)==3 and int(conf[0])>0:
            cdir = os.path.join(d,"0")
            for i in range(0, int(conf[0])):
                dir = os.path.join(d,str(i))
                mkdir(dir)
                for i in range(int(conf[1])):
                    create_hashfile(dir,size=int(conf[2]))
    return cdir

def get_workdir(d):
    cdir = d
    if fullsyncdir!=None:
        conf = fullsyncdir.split('/')
        if len(conf)==3 and int(conf[0])>0:
            cdir = os.path.join(d,"0")
    return cdir

def eval_excudetime(excludetime):
    if excludetime:   
        return "exclude_time"
    else:
        return None

