
import os
import time
import tempfile

__doc__ = """ Each of storm_nuploaders creates storm_nfiles and syncs them at the same time to the same account. Each of storm_ndownloaders downloads the files at the same time, verifies integrity of files and completness of sync. 
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

# Files created by each uploader
storm_nfiles = int(config.get('storm_nfiles',10))

# Number of workers (uploading files)
storm_nuploaders = int(config.get('storm_nuploaders',10))

# Number of workers (downloading files)
storm_ndownloaders = int(config.get('storm_ndownloaders',10))

# Verbose flag
storm_verbose = bool(config.get('storm_verbose',False))

# File size. None = default size/distribution.
storm_filesize = config.get('storm_filesize',None)

testsets = [
        { 'storm_nfiles': 10,
         'storm_nuploaders': 10,
         'storm_ndownloaders': 10,
         'storm_verbose': False,
         'storm_filesize': None
        }
]
def uploader(step):
    
    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)
    logger.info('Repository has %d files', k0)

    step(2,'Add files')
    logger.info('Adding %d files',storm_nfiles)
    for i in range(storm_nfiles):
        if storm_verbose: logger.info('Prepare file %d with storm_filesize %d',i,storm_filesize)
        create_hashfile(d,size=storm_filesize)

    run_ocsync(d)
    logger.info('Step 2 ends here...')

    step(3,None)
    return

for i in range(storm_nuploaders):
    add_worker(uploader,name="uploader%02d"%(i+1))

@add_worker
def initializer(step):

    reset_owncloud_account()
    reset_rundir()


def downloader(step):    
    step(1,'Active clients are syncing...')
    d = make_workdir()
    run_ocsync(d)

    k0 = count_files(d)
    logger.info('Repository has %d files',k0)

    step(2,'Active clients are uploading files...')

    step(3,'Download and check')

    sleep(1) # avoid race condition reading the file which has yet not been properly closed after writing

    run_ocsync(d)

    (ntot,nana,nbad) = analyse_hashfiles(d)

    etot = k0 + storm_nfiles * storm_nuploaders
    error_check(etot == ntot,'Missing files (files at start %d, expected %d, found %d)'%(k0,etot,ntot))
    fatal_check(nbad == 0, 'Corrupted files found (%d)'%nbad)

for i in range(storm_ndownloaders):
    add_worker(downloader,name="downloader%02d"%(i+1))
