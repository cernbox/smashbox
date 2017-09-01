import os
import time
import tempfile


__doc__ = """ Check mtime (and other timestamps) propagation via sync client.

Optional sleep parameter sets the additional delay between upload and download steps.

"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.utilities import reflection

sleep = int(config.get('mtimes_sleep',0)) 

import random

testsets = [ { 'mtimes_sleep' : 0 }, { 'mtimes_sleep' : 1 }, { 'mtimes_sleep' : 5 }, { 'mtimes_sleep' : random.random()*10 } ]

def log_times(**kwds):
    for k in sorted(kwds.keys()):
        st = kwds[k]
        logger.info("%15s atime %f mtime %f ctime %f", k,st.st_atime,st.st_mtime,st.st_ctime)


@add_worker
def worker0(step):    

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    shared = reflection.getSharedObject()

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    # TODO: add OS-type and fstype information, e.g. sources: /etc/mtab; df -T -P

    fn = "TIMESTAMP-TEST.DAT"
    absfn = os.path.join(d,fn)
    shared['filename'] = fn

    step(2,'Add new file')

    create_hashfile(d,fn,size=1000)

    stat_before = os.stat(absfn)
    run_ocsync(d)
    stat_after = os.stat(absfn)
    shared['source_stat'] = stat_after

    log_times(stat_before=stat_before,stat_after=stat_after)
    assert(stat_before == stat_after) # paranoia check, sync client should not modify local source file

    step(4,'Add a new version (new local inode)')

    create_hashfile(d,fn,size=1000)
    run_ocsync(d)
    shared['source_stat'] = os.stat(absfn)


    step(6,'Add a new version (same local inode)')

    modify_file(absfn,'x',1,100) # append to existing file
    run_ocsync(d)
    shared['source_stat'] = os.stat(absfn)


        
@add_worker
def worker1(step):

    shared = reflection.getSharedObject()

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)

    step(2,'Resync and check files added by worker0')

    fn = shared['filename']

    for k in [3,5,7]:
        step(k,'Resync and check files added by worker0')

        time.sleep(sleep)

        run_ocsync(d)

        dest = os.stat(os.path.join(d,fn))
        source = shared['source_stat']

        log_times(source=source,dest=dest)

        error_check(dest.st_mtime == round(dest.st_mtime), "Propagated mtime gets rounded up to the nearest second" ) 
        error_check(abs(source.st_mtime-dest.st_mtime) <= 1.0, 'Expecting not too have more than 1s difference on mtime') # NOT TRUE!




        



    





