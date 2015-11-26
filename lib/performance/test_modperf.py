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

nfiles = int(config.get('%s_nfiles'%test_name,1))
filesize = config.get('%s_filesize'%test_name,1000)
fraction = config.get('%s_add_orgn_fraction'%test_name,0.1)
excludetime = config.get('%s_excludetime'%test_name,True)
full_dir_size = "10/100/10000"
fullsyncdir = config.get('%s_fullsyncdir'%test_name,full_dir_size)
hashfiles = config.get('%s_hashfiles'%test_name,True)

if type(filesize) is type(''):
    filesize = eval(filesize)
testsets = [
#Modify sync - twice per day, every second day - all clients - packet sniffer on#
        { 
         '%s_filesize'%test_name: 1000,
        },#0
        { 
         '%s_filesize'%test_name: 5000000,
         '%s_add_orgn_fraction'%test_name:0.1,#it will add block of data of size 10% of original file
        },#1
        { 
         '%s_filesize'%test_name: 5000000,
         '%s_add_orgn_fraction'%test_name:0.5,#it will add block of data of size 50% of original file
        },#2
        { 
         '%s_filesize'%test_name: 5000000,
         '%s_add_orgn_fraction'%test_name:1,#it will add block of data of size 1000% of original file
        },#3
        { 
         '%s_filesize'%test_name: 500000000, 
        },#4
##############
#Modify sync - twice per day, every second day - owncloud clients only - packet sniffer off#
        { 
         '%s_filesize'%test_name: 500000, 
        },#5
        { 
         '%s_filesize'%test_name: 50000000,
        },#6
##############
]

@add_worker
def worker0(step): 
    
    exclude_time = eval_excludetime()
    
    step(1,'Preparation')
    d = make_workdir()
    array = prepare_workdir(d)
    count_dir = array[0]
    d = array[1]
    mod_file_array = []
    for i in range(nfiles):
        mod_file_array.append(create_test_file(count_dir,"%s%s"%("test",i),filesize))
    run_ocsync(d,option=exclude_time)
    
    k0,ncorrupt0 = check_workdir(d)

    step(4,'Modify files')
    for j in range(0, len(mod_file_array)):
        modify_dummy_file(mod_file_array[j],filesize*fraction)

    run_ocsync(d)
    
    k1,ncorrupt1 = check_workdir(d)

    error_check(k1==k0,'Expecting to have %d files more: see k1=%d k0=%d'%((k0-k1),k1,k0))
    fatal_check((ncorrupt0+ncorrupt1)==0, 'Corrupted files (%s) found'%(ncorrupt0+ncorrupt1))
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
    k0,ncorrupt0 = check_workdir(d)

    step(5,'Resync and check files modified by worker0')

    run_ocsync(d)

    k1,ncorrupt1 = check_workdir(d)

    error_check(k1==k0,'Expecting to have %d files more: see k1=%d k0=%d'%((k0-k1),k1,k0))
    fatal_check((ncorrupt0+ncorrupt1)==0, 'Corrupted files (%s) found'%(ncorrupt0+ncorrupt1))

""" TEST UTILITIES """
   
def prepare_workdir(d):
    cdir = os.path.join(d,"0")
    remove_tree(cdir)
    if fullsyncdir!=False:
        conf = fullsyncdir.split('/')
        if len(conf)==3 and int(conf[0])>0:
            for i in range(0, int(conf[0])):
                dir = os.path.join(d,str(i)) 
                if (not (os.path.exists(dir))) or i==0:
                    mkdir(dir)
                    for j in range(int(conf[1])):
                        create_test_file(dir,"%s%s"%(i,j),int(conf[2]))
            return [cdir,d]
    reset_owncloud_account()
    reset_rundir()
    mkdir(wdir)
    return [cdir,d]

def get_workdir(d):
    cdir = os.path.join(d,"0")
    remove_tree(cdir)  
    mkdir(cdir)
    return [cdir,d]

def eval_excludetime():
    global excludetime
    if excludetime:   
        return "exclude_time"
    else:
        return None

def create_test_file(directory, name, size, bs=None):
    if hashfiles==True:
        if bs==None:
            fn = create_hashfile(directory,size=size,bs=size)
        else:
            fn = create_hashfile(directory,size=size,bs=bs)
    else:
        fn = create_dummy_file(directory,name,size,bs=bs)
    return fn

def check_workdir(d):
    files = 0
    corrupt = 0
    if fullsyncdir!=False:
        conf = fullsyncdir.split('/')   
        sync_dir_num = int(conf[0])
    else:
        sync_dir_num = 1
    for n in range(sync_dir_num):
        dir = os.path.join(d,str(n)) 
        nfiles,nanalysed,ncorrupt = analyse_hashfiles(dir)
        files += nfiles
        corrupt += ncorrupt
    return (files,corrupt)