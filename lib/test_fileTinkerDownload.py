import os
import time
import tempfile


__doc__ = """ Create/modify a file locally while a file with the same name gets downloaded from the server.
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

fileTinkerDownload_tinker_wait = int(config.get('fileTinkerDownload_tinker_wait',2))
fileTinkerDownload_filesize = int(config.get('fileTinkerDownload_filesize',300000000))

if type(fileTinkerDownload_filesize) is type(''):
    fileTinkerDownload_filesize = eval(fileTinkerDownload_filesize)

testsets = [
        { 'fileTinkerDownload_filesize': 300000000, 
          'fileTinkerDownload_tinker_wait': i
        } for i in range(1,5) ]


@add_worker
def worker0(step):    

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    step(2,'Add a file: fileTinkerDownload_filesize=%s'%fileTinkerDownload_filesize)

    create_hashfile(d,filemask='TINKER.DAT',size=fileTinkerDownload_filesize)

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
    d = make_workdir('worker1') # use the same workdir as worker1

    step(3,'Tinker with the file while the worker1 downloads')
    
    sleep(fileTinkerDownload_tinker_wait)

    fn,md5 = create_hashfile2(d,filemask='TINKER.DAT',size=fileTinkerDownload_filesize)

    step(4) # worker1 ended syncing

    error_check(md5sum(fn) == md5)


    



