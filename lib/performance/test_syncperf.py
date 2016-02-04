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

testdirstruct = config.get('%s_testdirstruct'%test_name,"0/1/1000")
excludetime = config.get('%s_excludetime'%test_name,True)
fullsyncdir = config.get('%s_fullsyncdir'%test_name,False)
hashfiles = config.get('%s_hashfiles'%test_name,False)
blocksize = config.get('%s_rptblocksize'%test_name,None)
countfiles = config.get('%s_countfiles'%test_name,True)

testsets = [
        #Test sync#
        {
          '%s_testdirstruct'%test_name:"0/1/1", #1B
          '%s_countfiles'%test_name:True,
        },#0
        ###########
        {
          '%s_testdirstruct'%test_name:"0/1/100000000", #100MB = 100MB
          '%s_countfiles'%test_name:True,
        },#1
        {
          '%s_testdirstruct'%test_name:"0/10/10000000",#10x10MB = 100MB
          '%s_countfiles'%test_name:True,
        },#2
        {
          '%s_testdirstruct'%test_name:"10/100/10000",#1000x100kB = 10MB
          '%s_countfiles'%test_name:True,
        },#3
        {
          '%s_testdirstruct'%test_name:"0/1/500000000",
          '%s_rptblocksize'%test_name:None, # file contains only random bytes
          '%s_fullsyncdir'%test_name:False,
        },#4
        {
          '%s_testdirstruct'%test_name:"0/1/500000000",
          '%s_rptblocksize'%test_name:1000*1000, # file contains repeated blocks of 1MB 
          '%s_fullsyncdir'%test_name:False,
        },#5
        {
          '%s_testdirstruct'%test_name:"0/1/500000000",
          '%s_rptblocksize'%test_name:4*1024*1024, # file contains only random bytes
          '%s_fullsyncdir'%test_name:False,
        },#6
#############
]

@add_worker
def worker0(step): 
    exclude_time = eval_excludetime()
    
    step(1,'Preparation')
    d = make_workdir()
    test_dir,sync_dir_num = prepare_workdir(d)
    run_ocsync(d,option=[exclude_time])
    k0,ncorrupt0 = check_workdir(d,test_dir,sync_dir_num)

    step(4,'Add %s files and check if we still have k1+nfiles after resync'%testdirstruct)
    nfiles = create_teststruct(test_dir)
    run_ocsync(d)
    k1,ncorrupt1 = check_workdir(d,test_dir,sync_dir_num)
    error_check(k1-k0==nfiles,'Expecting to have %d files, have %d: see k1=%d k0=%d'%(nfiles,k1-k0,k1,k0))
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
    run_ocsync(d,option=[exclude_time])
    k0,ncorrupt0 = check_workdir(d,test_dir,sync_dir_num)

    step(5,'Resync and check files added by worker0')
    run_ocsync(d)
    k1,ncorrupt1 = check_workdir(d,test_dir,sync_dir_num)
    error_check(k1-k0==nfiles,'Expecting to have %d files, have %d: see k1=%d k0=%d'%(nfiles,k0-k1,k1,k0))
    fatal_check((ncorrupt0+ncorrupt1)==0, 'Corrupted files (%s) found'%(ncorrupt0+ncorrupt1))

""" TEST UTILITIES """
    
def prepare_workdir(d):
    wdir = os.path.join(d,"0")
    if fullsyncdir!=False:
        conf = fullsyncdir.split('/')
        if len(conf)==3 and int(conf[0])>0:
            for i in range(0, int(conf[0])):
                dir = os.path.join(d,str(i)) 
                if (not (os.path.exists(dir))):
                    mkdir(dir)
                    for j in range(int(conf[1])):
                        create_test_file(dir,"%s%s"%(i,j),int(conf[2]))
            return (wdir,int(conf[0]))
        error_check(len(conf)==3,'Improper testdirstruct format, expects dir_n/file_n/file_size')
    mkdir(wdir)
    return (wdir,1)

def get_workdir(d):
    wdir = os.path.join(d,"0")
    dir_num = 1
    if fullsyncdir!=False:
        conf = fullsyncdir.split('/') 
        if len(conf)==3 and int(conf[0])>0:
            return (wdir,int(conf[0]))
        error_check(len(conf)==3,'Improper workdirstruct format, expects dir_n/file_n/file_size')
    return (wdir,1)

def create_teststruct(test_dir):
    teststruct = testdirstruct.split('/')
    nfiles = 0
    error_check(len(teststruct)==3,'Improper teststruct format, expects dir_n/file_n/file_size')
    if int(teststruct[0])<1:
        mkdir(test_dir)
        for i in range(int(teststruct[1])):
            create_test_file(test_dir,"%s%s%s"%(0,"test",i),int(teststruct[2]),bs=blocksize)
            nfiles+=1
    else:
        for i in range(int(teststruct[0])):
            dir = os.path.join(test_dir,str(i)) 
            mkdir(dir)
            for j in range(int(teststruct[1])):
                create_test_file(dir,"%s%s%s"%(i,"test",j),int(teststruct[2]),bs=blocksize)
                nfiles+=1
    return nfiles

def eval_teststruct():
    teststruct = testdirstruct.split('/')
    nfiles = 0
    error_check(len(teststruct)==3,'Improper teststruct format, expects dir_n/file_n/file_size')
    if int(teststruct[0])<1:
        for i in range(int(teststruct[1])):
            nfiles+=1
    else:
        for i in range(int(teststruct[0])):
            for j in range(int(teststruct[1])):
                nfiles+=1
    return nfiles

def create_test_file(directory, name, size, bs=None):
    if hashfiles==True:
        if bs==None:
            create_hashfile(directory,size=size,bs=size)
        else:
            create_hashfile(directory,size=size,bs=bs)
    else:
        create_dummy_file(directory,name,size,bs=bs)


def check_workdir(d,test_dir,sync_dir_num):
    teststruct = testdirstruct.split('/')
    error_check(len(teststruct)==3,'Improper teststruct format, expects dir_n/file_n/file_size')
    files = 0
    corrupt = 0
    for i in range(int(teststruct[0])):
        dir = os.path.join(test_dir,str(i)) 
        nfiles,nanalysed,ncorrupt = analyse_hashfiles(dir)
        files += nfiles
        corrupt += ncorrupt
        
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

