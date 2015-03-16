import os
import time
import tempfile

__doc__ = """ Add nfiles to a directory (two clients) and check consistency after synch.
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

nfiles = int(config.get('nplustwo_nfiles',10))

@add_worker
def setup(step):
    reset_owncloud_account()
    reset_rundir()

def adder(step):

    step(1,'Preparation')
    d = make_workdir()

    run_ocsync(d)
    k0 = count_files(d)

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    for i in range(nfiles):
        create_hashfile(d,size=config.hashfile_size)

    run_ocsync(d)

    step(3,'Get other files from server and check')

    run_ocsync(d)
    (ntot,k1,ncorruptions) = analyse_hashfiles(d)

    error_check(k1-k0==2*nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))
    error_check(ncorruptions==0,'After synch %d corrupted files found'%(ncorruptions))

    logger.info('SUCCESS: %d files found',k1)

@add_worker
def worker0(step):
    adder(step)
        
@add_worker
def worker1(step):
    adder(step)

