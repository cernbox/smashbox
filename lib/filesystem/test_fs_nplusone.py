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


if type(filesize) is type(''):
    filesize = eval(filesize)


testsets = []

# create cartesian product of all test configurations
for s in [[1000, 100], [OWNCLOUD_CHUNK_SIZE(0.3), 10], [OWNCLOUD_CHUNK_SIZE(1.3), 2], [OWNCLOUD_CHUNK_SIZE(3.5), 1], [(3.5,1.37), 10]]:
  for t in [None, config.get('fs_nplusone_path0',"")]:
      for p in [None, config.get('fs_nplusone_path1',"")]:
          testsets.append( { 'fs_nplusone_filesize':s[0],
                             'fs_nplusone_nfiles':s[1],
                             'fs_nplusone_fspath0':t, 
                             'fs_nplusone_fspath1':p } )

@add_worker
def worker0(step):    

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    
    if fspath0:
        os.path.normpath(fspath0)
        d = os.path.join(fspath0,config['oc_server_folder'])
    else:
        d = make_workdir()
        run_ocsync(d)
    

    k0 = count_files(d)

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    for i in range(nfiles):
        logger.info('file number {}'.format(i+1)) 
        create_hashfile(d,size=filesize)
        
    if not fspath0:
        run_ocsync(d)

    #delay between the 2 mount points. when one worker add files via mount point the other have to wait few seconds to see them
    sleep(3)
        
    ncorrupt = analyse_hashfiles(d)[2]
    
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    logger.info('SUCCESS: %d files found',k1)
        
@add_worker
def worker1(step):
    step(1,'Preparation')

    if fspath1:
        os.path.normpath(fspath1)
        d = os.path.join(fspath1,config['oc_server_folder'])
    else:
        d = make_workdir()
        run_ocsync(d)

    k0 = count_files(d)

    step(3,'Resync and check files added by worker0')

    if not fspath1:
        run_ocsync(d)


    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)




