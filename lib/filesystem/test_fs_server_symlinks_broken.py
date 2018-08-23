import os
import time
import tempfile


__doc__ = """ Check what happens with broken symlinks on the server.
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

#fspath = config.get('fs_server_symlinks_path','/eos/dockertest/user/%s/%s'%(config['oc_account_name'][0],config['oc_account_name']))
fspath = config.get('fs_server_symlinks_path','/eos/user/%s/%s'%(config['oc_account_name'][0],config['oc_account_name']))

@add_worker
def worker0(step):    

    # cleanup all local files for the test
    reset_owncloud_account()
    reset_rundir()

    step(1,'Preparation')

    d = os.path.join(fspath,config['oc_server_folder'])

    f1 = create_hashfile(d,size=10)
    f2 = create_hashfile(d,size=20)

    f1=os.path.basename(f1)
    f2=os.path.basename(f2)

    link_path = os.path.join(d,'link.file.rel.%s'%f1)
    link = os.symlink(f1,link_path)

    step(2,'First sync')

    # Synchronize the content locally

    syncd = make_workdir()
    run_ocsync(syncd)

    def check_all_good(N):
        ncorrupt = analyse_hashfiles(syncd)[2]
        fatal_check(ncorrupt==0, 'Corrupted files (%s) found in path %s'%(ncorrupt,syncd))
        error_check(count_files(syncd)==N,'Expecting to have exactly %d entries'%N)

    check_all_good(N=3)

    step(3,'When a symlink becomes broken on the server the file is removed locally')

    os.remove(link_path)
    link = os.symlink('nirvana/does/not/exist',link_path)

    syncd = make_workdir()
    run_ocsync(syncd)
    
    check_all_good(N=2) # BROKEN SYMLINKS GET REMOVED LOCALLY

    step(4,'Synchronization should continue to work inspite of broken server links')

    f3=create_hashfile(d,size=30)
    f3=os.path.basename(f3)

    run_ocsync(syncd)
    
    fatal_check(os.path.exists(os.path.join(syncd,f3)))

    check_all_good(N=3) # Sync continues and new file is downloaded


