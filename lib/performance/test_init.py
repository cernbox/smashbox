import os
import time
import tempfile


__doc__ = """ Add nfiles to a directory and check consistency.

    "syncperf_fullsyncdir" is defined as (number of directories) / (number of files) / (size of files) 
        - if not in the correct format, it will execute with empty directory.
    
    "excludetime" is information if to count preparation sync to the total sync time.
    
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *
import inspect
test_name = ((os.path.basename(inspect.getfile(inspect.currentframe()))).replace('test_','')).replace('.py','')

excludetime = config.get('%s_excludetime'%test_name,True)
hashfiles = config.get('%s_hashfiles'%test_name,True)
blocksize = config.get('%s_rptblocksize'%test_name,None)
countfiles = config.get('%s_countfiles'%test_name,True)
testdirstruct = config.get('%s_testdirstruct'%test_name,False)

testsets = [
        {
        },#0
        ]    

@add_worker
def worker0(step): 
    exclude_time = eval_excludetime()
    
    step(1,'Preparation')
    d = make_workdir()
    test_dir,sync_dir_num = prepare_workdir(d)
    run_ocsync(d,option=exclude_time)
        
@add_worker
def worker1(step):
    exclude_time = eval_excludetime()
    
    step(2,'Preparation')
    d = make_workdir()
    test_dir,sync_dir_num = get_workdir(d)
    run_ocsync(d,option=exclude_time)

""" TEST UTILITIES """
    
def prepare_workdir(d):
    reset_owncloud_account()
    wdir = os.path.join(d,"0")
    reset_rundir()
    mkdir(wdir)
    return (wdir,1)

def get_workdir(d):
    wdir = os.path.join(d,"0")
    return (wdir,1)

def eval_excludetime():
    global excludetime
    if excludetime:   
        return "exclude_time"
    else:
        return None

