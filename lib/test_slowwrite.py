import os
import time
import tempfile


__doc__ = """ 

Synchronize local folder while writing into the file.

This is a testcase for:

https://github.com/owncloud/mirall/issues/2210 (corrupted file upload if file modified during transfer)

"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

MB = 1024*1000

filesizeKB = int(config.get('slowwrite_filesizeKB',10000))
blockSize = int(config.get('slowwrite_blockSize',MB))
slowWrite = int(config.get('slowwrite_slowWrite',1))

nfiles=1

testsets = [
        { 'slowwrite_filesizeKB': 2, 
          'slowwrite_blockSize': 200,
          'slowwrite_slowWrite':1
        },

        { 'slowwrite_filesizeKB': 5000, 
          'slowwrite_blockSize': MB,
          'slowwrite_slowWrite':1
        },


        { 'slowwrite_filesizeKB': 50000, 
          'slowwrite_blockSize': MB,
          'slowwrite_slowWrite':1
        }
]

@add_worker
def writer(step):    

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    d = make_workdir('writer') # bother writer and synchronizer share the same workdir
    run_ocsync(d)
    k0 = count_files(d)

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    create_hashfile(d,size=filesizeKB*1000,bs=blockSize,slow_write=slowWrite) #config.hashfile_size)

@add_worker
def synchronizer(step):

    step(2,'Sync the file as it is being written by writer')

    sleep(slowWrite)
    d = make_workdir('writer') # bother writer and synchronizer share the same workdir
    run_ocsync(d)

    
@add_worker
def checker(step):

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    step(3,'Resync and check files added by synchronizer')

    run_ocsync(d)

    analyse_hashfiles(d)
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))




