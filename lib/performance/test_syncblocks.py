import os
import time
import tempfile


__doc__ = """ Add nfiles to a directory and check consistency.
    "excludetime" is information if to count preparation sync to the total sync time.
    Due to several engines being used, and possible running of other performance tests,
     there is need for so called sync_directory d and count directory for corruption and consistencty
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *
import inspect
test_name = ((os.path.basename(inspect.getfile(inspect.currentframe()))).replace('test_','')).replace('.py','')
nfiles = int(config.get('%s_nfiles'%test_name,1))
filesize = config.get('%s_filesize'%test_name,1000)
blocksize = config.get('%s_rptblocksize'%test_name,1000000)
excludetime = True

if type(filesize) is type(''):
    filesize = eval(filesize)
    
testsets = [
        { '%s_filesize'%test_name: 1000, 
          '%s_nfiles'%test_name:1,
          '%s_rptblocksize'%test_name:1024*1024,
        },
        { '%s_filesize'%test_name: 5000000, 
          '%s_nfiles'%test_name:1,
          '%s_rptblocksize'%test_name:1024*1024,
        },
        { '%s_filesize'%test_name: 500000000, 
          '%s_nfiles'%test_name:1,
          '%s_rptblocksize'%test_name:1024*1024,
        },
        { '%s_filesize'%test_name: 1000, 
          '%s_nfiles'%test_name:1,
          '%s_rptblocksize'%test_name:1000*1000,
        },
        { '%s_filesize'%test_name: 5000000, 
          '%s_nfiles'%test_name:1,
          '%s_rptblocksize'%test_name:1000*1000,
        },
        { '%s_filesize'%test_name: 500000000, 
          '%s_nfiles'%test_name:1,
          '%s_rptblocksize'%test_name:1000*1000,
        },
]

@add_worker
def worker0(step): 
    exclude_time = eval_excludetime()
    step(1,'Preparation')
    d = make_workdir()
    array = prepare_workdir(d)
    count_dir = array[0]
    d = array[1]
    step(2,'Pre-sync')
    run_ocsync(d,option=exclude_time)
    
    k0 = count_files(count_dir)

    step(4,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    for i in range(nfiles):
        create_dummy_file(count_dir,"%s%s"%("test",i),filesize,1000*1000)

    run_ocsync(d)

    
    k1 = count_files(count_dir)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    logger.info('SUCCESS: %d files found',k1)
        
@add_worker
def worker1(step):
    exclude_time = eval_excludetime()
    step(2,'Preparation')
    d = make_workdir()
    array = get_workdir(d)
    count_dir = array[0]
    d = array[1]
    step(3,'Pre-sync')
    run_ocsync(d,option=exclude_time)
    k0 = count_files(count_dir)

    step(5,'Resync and check files added by worker0')

    run_ocsync(d)

    k1 = count_files(count_dir)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))
    
def prepare_workdir(d):
    cdir = os.path.join(d,"0")
    remove_tree(cdir)
    reset_owncloud_account()
    mkdir(cdir)
    d = cdir
    return [cdir,d]

def get_workdir(d):
    cdir = os.path.join(d,"0")
    remove_tree(cdir)  
    mkdir(cdir)
    d = cdir  
    return [cdir,d]
    
    
def eval_excludetime():
    global excludetime
    if excludetime:   
        return "exclude_time"
    else:
        return None

