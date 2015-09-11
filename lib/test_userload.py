
import os
import time
import tempfile

__doc__ = """ One uploader, n downloaders. Uploader creates nfiles and syncs them at the same time to the same account. The checker verifies integrity of files and completness of sync. 
"""


# Files created by the uploader
nfiles = int(config.get('userload_nfiles',5))
# Number of downloaders
nworkers = int(config.get('userload_nworkers',10))
# Verbose flag
verbose = bool(config.get('userload_verbose',False))

testsets = [
        { 'userload_nfiles': 5,
         'userload_nworkers': 10,
         'userload_verbose': False
        }
]


hash_filemask = 'hash_{md5}'

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

@add_worker
def uploader(step):

    reset_owncloud_account()
    reset_rundir()
    
    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d,filemask=hash_filemask)
    logger.info('Repository has %d files', k0)

    step(2,'Add files')
    logger.info('Adding %d files',nfiles)
    for i in range(nfiles):
        if verbose: logger.info('Prepare file %d',i)
        create_hashfile(d,filemask=hash_filemask)
    run_ocsync(d)
    logger.info('Step 2 ends here...')

    step(3,None)
    return


def downloader(step):
    
    step(1,'Active clients are syncing...')
    d = make_workdir()
    run_ocsync(d)

    k0 = count_files(d,filemask=hash_filemask)
    logger.info('Repository has %d files',k0)

    step(2,'Download in parallel to upload...')

    run_ocsync(d)

    step(3,'Final download and check')

    run_ocsync(d)

    (ntot,nana,nbad) = analyse_hashfiles(d,filemask=hash_filemask)

    etot = k0 + nfiles
    error_check(etot == ntot,'Missing files (files at start %d, expected %d, found %d)'%(k0,etot,ntot))


for i in range(nworkers):
    add_worker(downloader,name="downloader%02d"%(i+1))

