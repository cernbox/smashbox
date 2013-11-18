
import os
import time
import tempfile

__doc__ = """ Each of nworkers (uploaders) creates nfiles and syncs them at the same time to the same account. The checker verifies integrity of files and completness of sync. 
"""


# Files created by each worker
nfiles = int(config.get('storm_nfiles',5))
# Number of workers (creating files)
nworkers = int(config.get('storm_nworkers',10))
# Verbose flag
verbose = bool(config.get('storm_verbose',False))

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

def uploader(step):
    
    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)
    logger.info('Repository has %d files', k0)

    step(2,'Add files')
    logger.info('Adding %d files',nfiles)
    for i in range(nfiles):
        if verbose: logger.info('Prepare file %d',i)
        create_hashfile(d)
    run_ocsync(d)
    logger.info('Step 2 ends here...')

    step(3,None)
    return

for i in range(nworkers):
    add_worker(uploader,name="uploader%02d"%(i+1))

@add_worker
def checker(step):

    reset_owncloud_account()
    reset_rundir()
    
    step(1,'Active clients are syncing...')
    d = make_workdir()
    run_ocsync(d)

    k0 = count_files(d)
    logger.info('Repository has %d files',k0)

    step(2,'Active clients are uploading files...')

    step(3,'Download and check')

    run_ocsync(d)

    (ntot,nana,nbad) = analyse_hashfiles(d)

    etot = k0 + nfiles * nworkers
    error_check(etot == ntot,'Missing files (files at start %d, expected %d, found %d)'%(k0,etot,ntot))


