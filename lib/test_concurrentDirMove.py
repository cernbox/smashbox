__doc__ = """

This test moves concurrently a directory ('mover' worker) while
files are added to it ('adder' worker) . The expected outcome is that
all added files are kept on the server and are found in the final directory.

"""



nfiles = int(config.get('concurrentMoveDir_nfiles',100))
filesize = int(config.get('concurrentMoveDir_filesize',10))
delaySeconds = int(config.get('concurrentMoveDir_delaySeconds',3)) # if delaySeconds > 0 then remover waits; else the adder waits;

from smashbox.utilities import *

testsets = [ 
    {'concurrentMoveDir_nfiles':100,
     'concurrentMoveDir_filesize':10,
     'concurrentMoveDir_delaySeconds':10 },  # removing the directory while lots of tiny files are uploaded

    {'concurrentMoveDir_nfiles':3,
     'concurrentMoveDir_filesize':OWNCLOUD_CHUNK_SIZE(1.1),
     'concurrentMoveDir_delaySeconds':5 },  # removing the directory while a large file is chunk-uploaded

    {'concurrentMoveDir_nfiles':20,
     'concurrentMoveDir_filesize':OWNCLOUD_CHUNK_SIZE(0.9),
     'concurrentMoveDir_delaySeconds':10 }, # removing the directory more but smaller files are uploaded

    {'concurrentMoveDir_nfiles':5,
     'concurrentMoveDir_filesize':OWNCLOUD_CHUNK_SIZE(0.1),
     'concurrentMoveDir_delaySeconds':-5 }, # removing the directory before files are uploaded

    {'concurrentMoveDir_nfiles':5,
     'concurrentMoveDir_filesize':OWNCLOUD_CHUNK_SIZE(2.1),
     'concurrentMoveDir_delaySeconds':-10 } # removing the directory before laarge files are chunk-uploaded

    ]

import time
import tempfile


from smashbox.utilities.hash_files import *

@add_worker
def creator(step):
    reset_owncloud_account()
    reset_rundir()

    step(1,'upload empty subdirectory')
    d = make_workdir()
    d2 = os.path.join(d,'subdir')
    mkdir(d2)
    run_ocsync(d)

    step(5,'final check')
    run_ocsync(d)
    final_check(d)

    
@add_worker
def adder(step):
    
    step(2,'sync the empty directory created by the creator')
    d = make_workdir()
    run_ocsync(d)

    step(3,'locally create content in the subdirectory')
    d2 = os.path.join(d,'subdir')

    for i in range(nfiles):
        create_hashfile(d2, size=filesize) #createfile_zero(os.path.join(d2,"test.%02d"%i),count=filesize, bs=1000)

    step(4,'sync the added files in parallel')
    if delaySeconds<0:
        sleep(-delaySeconds)
    run_ocsync(d,n=2)

    step(5,'final check')
    run_ocsync(d)
    final_check(d)


@add_worker
def mover(step):
    step(2,'sync the empty directory created by the creator')
    d = make_workdir()
    run_ocsync(d)

    step(3,'locally rename subdir to subdir2')
    s1 = os.path.join(d,'subdir')
    s2 = os.path.join(d,'subdir2')
    os.rename(s1,s2)

    step(4,'sync the subdir2 in parallel')
    if delaySeconds>0:
        sleep(delaySeconds)
    run_ocsync(d)

    step(5,'final check')
    run_ocsync(d)
    final_check(d)

@add_worker
def checker(step):

    step(5,'sync the final state of the repository into a fresh local folder')
    d = make_workdir()
    run_ocsync(d)

    final_check(d)


def final_check(d):

    list_files(d,recursive=True)

    d2 = os.path.join(d,'subdir2')
    
    logger.info('final output: %s',d2)

    all_files,analysed_files,bad_files = analyse_hashfiles(d2)

    error_check(bad_files == 0,'%s corrupted files in %s'%(bad_files,d2))
    error_check(analysed_files == nfiles,"not all files are present (%d/%d)"%(nfiles,analysed_files)) # FIXME: well, there may be other files - we don't check that yet


    #runcmd('find %s'%d)

    #log('content of /subdir as reported by webdav')
    #list_webdav_propfind('subdir')


