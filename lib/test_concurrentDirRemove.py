__doc__ = """

This test removes concurrently a directory ('remover' worker) while
files are added to it ('adder' worker) . 

According to Webdav specs, PUT into inexisting path does not create missing directories but returns 409 (Conflict). 

Cernbox/EOS: Hence the expected outcome is that part of the files that was already uploaded gets deleted.

OwnCloud7? : For PUT which creates the missing directories the expected outcome is that all added files are kept on the server.

"""

nfiles = int(config.get('concurrentRemoveDir_nfiles',10))
filesizeKB = int(config.get('concurrentRemoveDir_filesizeKB',9000))
delaySeconds = int(config.get('concurrentRemoveDir_delaySeconds',3)) # if delaySeconds > 0 then remover waits; else the adder waits;

testsets = [ 
    {'concurrentRemoveDir_nfiles':3,
     'concurrentRemoveDir_filesizeKB':10000,
     'concurrentRemoveDir_delaySeconds':5 },  # removing the directory while a large file is chunk-uploaded

    {'concurrentRemoveDir_nfiles':40,
     'concurrentRemoveDir_filesizeKB':9000,
     'concurrentRemoveDir_delaySeconds':5 }, # removing the directory while lots of smaller files are uploaded

    {'concurrentRemoveDir_nfiles':5,
     'concurrentRemoveDir_filesizeKB':15000,
     'concurrentRemoveDir_delaySeconds':-5 } # removing the directory before files are uploaded

    ]

import time
import tempfile

from smashbox.utilities import *
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
        create_hashfile(d2, size=filesizeKB*1000) #createfile_zero(os.path.join(d2,"test.%02d"%i),count=filesizeKB, bs=1000)

    step(4,'sync the added files in parallel')
    if delaySeconds<0:
        sleep(-delaySeconds)
    run_ocsync(d)

    step(5,'final check')
    run_ocsync(d)


@add_worker
def remover(step):
    step(2,'sync the empty directory created by the creator')
    d = make_workdir()
    run_ocsync(d)

    step(3,'locally remove subdir')
    d2 = os.path.join(d,'subdir')
    remove_tree(d2)

    step(4,'sync the removed subdir in parallel')
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

    d2 = os.path.join(d,'subdir')
    
    logger.info('final output: %s',d2)

    all_files,analysed_files,bad_files = analyse_hashfiles(d2)

    error_check(bad_files == 0,'%s corrupted files in %s'%(bad_files,d2))
    
    #it is hard to determine how many files should be present with 409 Conflict behaviour
    #error_check(analysed_files == nfiles,"not all files are present (%d/%d)"%(analysed_files,nfiles)) # FIXME: well, there may be other files - we don't check that yet


    #runcmd('find %s'%d)

    #log('content of /subdir as reported by webdav')
    #list_webdav_propfind('subdir')


