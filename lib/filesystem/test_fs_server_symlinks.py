import os
import time
import tempfile


__doc__ = """ Check symlinks on the server: basic operations which involve absolute and relative symlinked files and directories.
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

    #print os.path.join(d,f1),os.path.join(d,'link.file.abs.%s'%f1)
    l1 = os.symlink(os.path.join(d,f1),os.path.join(d,'link.file.abs.%s'%f1))
    l2 = os.symlink(f2,os.path.join(d,'link.file.rel.%s'%f2))

    subd = os.path.join(d,'subdir')
    os.mkdir(subd)

    os.symlink(os.path.join('..',f1), os.path.join(subd,f1))
    os.symlink(os.path.join(d,f2), os.path.join(subd,f2))

    create_hashfile(subd,size=30)
    create_hashfile(subd,size=40)

    ldir1 = os.symlink(subd,os.path.join(d,'link.dir.abs'))
    ldir2 = os.symlink('subdir',os.path.join(d,'link.dir.rel'))

    step(2,'First sync')

    # Synchronize the content locally

    syncd = make_workdir()
    run_ocsync(syncd)

    def check_subdir_count(N):
        error_check(count_files(os.path.join(syncd,'subdir'))==N,'Expecting to have exactly %d entries'%N)
        error_check(count_files(os.path.join(syncd,'link.dir.abs'))==N,'Expecting to have exactly %d entries'%N)
        error_check(count_files(os.path.join(syncd,'link.dir.rel'))==N,'Expecting to have exactly %d entries'%N)

    def check_all_corrupt():
        def c(path):
            ncorrupt = analyse_hashfiles(path)[2]
            fatal_check(ncorrupt==0, 'Corrupted files (%s) found in path %s'%(ncorrupt,path))
        c(syncd)
        c(os.path.join(syncd,'subdir'))
        c(os.path.join(syncd,'link.dir.abs'))
        c(os.path.join(syncd,'link.dir.rel'))

    # Symlinks are followed on the server and are undistinguishable from normal files for the sync client
    error_check(count_files(syncd)==4,'Expecting to have exactly 4 files')

    check_subdir_count(4)
    check_all_corrupt()

    ### File created directly on the server

    step(3,'Create new server file')

    f3=create_hashfile(subd,size=50)

    run_ocsync(syncd,n=2) # need to run twice to properly reflect the changes via symlinks

    # The file created in the symlinked subdirectory should be visible via all symlinks to this directory
    # And thus should be downloaded multiple times into these symlinked areas
    check_subdir_count(5)
    check_all_corrupt()

    ### File removed directly on the server

    step(4,'Remove local file')

    # The delete should also be propagated accordingly
    os.remove(f3)
    run_ocsync(syncd)

    check_subdir_count(4)
    check_all_corrupt()


    ### File created on the sync client

    step(5,'Create new local file')

    f4=create_hashfile(os.path.join(syncd,"subdir"),size=50)

    run_ocsync(syncd,n=2) # need to run twice to properly reflect the changes via symlinks

    # The file created in the symlinked subdirectory should be visible via all symlinks to this directory
    # And thus should be downloaded multiple times into these symlinked areas
    check_subdir_count(5)
    check_all_corrupt()

    ### File removed directly on the server

    step(6,'Remove server file')

    # The delete should also be propagated accordingly
    os.remove(f4)
    run_ocsync(syncd,n=2) # need to run twice to properly reflect the changes via symlinks

    check_subdir_count(4)
    check_all_corrupt()
