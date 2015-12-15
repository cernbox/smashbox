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

KB=1024
MB=1024*KB

testsets = [
        #Test sync#
        {
          '%s_testdirstruct'%test_name:"0/100/var", #1kB
          '%s_countfiles'%test_name:True,
        },#0
        ]    
files = [[1,50*MB],
            [1,15*MB],[1,1*MB],[1,2*MB],[1,3*MB],[1,4*MB],[1,5*MB],[1,8*MB],[1,10*MB], [11,500*KB],
        [32,50*KB],
        [28,5*KB],
        [15,1*KB],
        [5,100]]

@add_worker
def worker0(step): 
    exclude_time = eval_excludetime()
    
    step(1,'Preparation')
    d = make_workdir()
    test_dir,sync_dir_num = prepare_workdir(d)
    run_ocsync(d,option=exclude_time)
    k0,ncorrupt0 = check_workdir(d,test_dir,sync_dir_num)

    step(4,'Add 100 files and check if we still have k1+nfiles after resync')
    nfiles = create_teststruct(test_dir)
    run_ocsync(d)
    k1,ncorrupt1 = check_workdir(d,test_dir,sync_dir_num)
    error_check(k1-k0==nfiles,'Expecting to have %d files, have %d: see k1=%d k0=%d missing=[%s]'%(nfiles,k1-k0,k1,k0,missing_in_teststruct(test_dir)))
    fatal_check((ncorrupt0+ncorrupt1)==0, 'Corrupted files (%s) found'%(ncorrupt0+ncorrupt1))
    logger.info('SUCCESS: %d files found',k1)
        
@add_worker
def worker1(step):
    exclude_time = eval_excludetime()
    
    step(2,'Preparation')
    d = make_workdir()
    test_dir,sync_dir_num = get_workdir(d)
    nfiles = eval_teststruct()
    
    step(3,'Pre-sync')
    run_ocsync(d,option=exclude_time)
    k0,ncorrupt0 = check_workdir(d,test_dir,sync_dir_num)

    step(5,'Resync and check files added by worker0')
    run_ocsync(d)
    k1,ncorrupt1 = check_workdir(d,test_dir,sync_dir_num)
    error_check(k1-k0==nfiles,'Expecting to have %d files, have %d: see k1=%d k0=%d missing=[%s]'%(nfiles,k1-k0,k1,k0,missing_in_teststruct(test_dir)))
    fatal_check((ncorrupt0+ncorrupt1)==0, 'Corrupted files (%s) found'%(ncorrupt0+ncorrupt1))

""" TEST UTILITIES """
    
def prepare_workdir(d):
    reset_owncloud_account()
    wdir = os.path.join(d,"0")
    reset_rundir()
    mkdir(wdir)
    return (wdir,1)

def get_workdir(d):
    wdir = os.path.join(d,"0")
    remove_tree(wdir)  
    mkdir(wdir)
    return (wdir,1)

def create_teststruct(test_dir):
    for x in files:
        for n in range(x[0]):
            create_test_file(test_dir,"%s%s%s"%(n,"test",x[1]),int(x[1]),bs=blocksize)
    return 100
def missing_in_teststruct(test_dir):
    flist = []
    for x in files:
        for n in range(x[0]):
            fname = "%s%s%s"%(n,"test",x[1])
            if not os.path.exists(os.path.join(test_dir,fname)):
               flist.append(fname) 
    return flist

def eval_teststruct():
    return 100

def create_test_file(directory, name, size, bs=None):
    if hashfiles==True:
        if bs==None:
            create_hashfile(directory,size=size,bs=size)
        else:
            create_hashfile(directory,size=size,bs=bs)
    else:
        create_dummy_file(directory,name,size,bs=bs)


def check_workdir(d,test_dir,sync_dir_num):
    files = 0
    corrupt = 0
        
    for n in range(sync_dir_num):
        dir = os.path.join(d,str(n)) 
        nfiles,nanalysed,ncorrupt = analyse_hashfiles(dir)
        files += nfiles
        corrupt += ncorrupt
    return (files,corrupt)

def eval_excludetime():
    global excludetime
    if excludetime:   
        return "exclude_time"
    else:
        return None

