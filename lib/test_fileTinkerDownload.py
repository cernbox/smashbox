import os
import time
import tempfile
import glob


__doc__ = """ Create/modify a file locally while a file with the same name gets downloaded from the server.

1.7 client has a bug and does not pass this test

2.1.1+ client detects the file being modified locally and restarts itself to complete the sync (which creates a conflict file)

$ egrep -e "Restarting|File has changed since discovery|CONFLICT" /tmp/smashdir/test_fileTinkerDownload/worker1-ocsync.step03.cnt000.log 

void OCC::SyncEngine::slotItemCompleted(const OCC::SyncFileItem&, const OCC::PropagatorJob&) "TINKER.DAT" INSTRUCTION_NEW 3 "File has changed since discovery" 
Restarting Sync, because another sync is needed 1 
[03/09 09:51:24.136284, 8] _csync_merge_algorithm_visitor:  INSTRUCTION_CONFLICT server file: TINKER.DAT
void OCC::SyncEngine::slotItemCompleted(const OCC::SyncFileItem&, const OCC::PropagatorJob&) "TINKER.DAT" INSTRUCTION_CONFLICT 5 "" 


"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

tinker_wait = int(config.get('fileTinkerDownload_tinker_wait',2))
filesize = config.get('fileTinkerDownload_filesize',300000000)

if type(filesize) is type(''):
    filesize = eval(filesize)

testsets = [
        { 'fileTinkerDownload_filesize': 300000000, 
          'fileTinkerDownload_tinker_wait': i
        } for i in range(1,5) ]


@add_worker
def worker0(step):    
    shared = reflection.getSharedObject()

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    step(2,'Add a file: filesize=%s'%filesize)


    fn,md5 = create_hashfile2(d,filemask='TINKER.DAT',size=filesize)

    shared['md5_worker0'] = md5

    run_ocsync(d)
        
@add_worker
def worker1(step):
    step(1,'Preparation')
    d = make_workdir('worker1')
    run_ocsync(d)
    k0 = count_files(d)

    step(3,'Sync the file down')
    run_ocsync(d)

    step(4)

@add_worker
def tinkerer(step):
    shared = reflection.getSharedObject()
    d = make_workdir('worker1') # use the same workdir as worker1

    step(3,'Tinker with the file while the worker1 downloads')
    
    sleep(tinker_wait)

    fn,md5 = create_hashfile2(d,filemask='TINKER.DAT',size=filesize)

    step(4) # worker1 ended syncing

    conflict_files = glob.glob(os.path.join(d,'TINKER_conflict-*-*.DAT'))

    fatal_check(len(conflict_files)==1, "expected exactly one conflict file, got %d (%s)"%(len(conflict_files),conflict_files))

    conflict_fn = conflict_files[0]

    error_check(md5sum(conflict_fn) == md5)  # locally changed file becomes the conflict file
    error_check(md5sum(fn) == shared['md5_worker0']) # checksum of the TINKER.DAT must much the one produced by other worker


    



