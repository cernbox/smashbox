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

testsets = [
#Typical sync - twice per day, every second day - all clients - packet sniffer on#
        {
          '%s_testdirstruct'%test_name:"0/1/1000",
          '%s_rptblocksize'%test_name:None,
        },#0
        {
          '%s_testdirstruct'%test_name:"0/1/5000000",
          '%s_rptblocksize'%test_name:None,
        },#1
        {
          '%s_testdirstruct'%test_name:"0/1/500000000",
          '%s_rptblocksize'%test_name:None, # file contains only random bytes
        },#2
        {
          '%s_testdirstruct'%test_name:"0/1/500000000",
          '%s_rptblocksize'%test_name:1000*1000, # file contains repeated blocks of 1MB 
        },#3
        {
          '%s_testdirstruct'%test_name:"0/1/500000000",
          '%s_rptblocksize'%test_name:4*1000*1000, # file contains repeated blocks of 4MB 
        },#4
        {
          '%s_testdirstruct'%test_name:"0/1/1000",
          '%s_fullsyncdir'%test_name:"10/100/10000",
          '%s_rptblocksize'%test_name:None,
        },#5
        {
          '%s_testdirstruct'%test_name:"0/1/5000000",
          '%s_fullsyncdir'%test_name:"10/100/10000",
          '%s_rptblocksize'%test_name:None,
        },#6
        {
          '%s_testdirstruct'%test_name:"0/1/500000000",
          '%s_fullsyncdir'%test_name:"10/100/10000",
          '%s_rptblocksize'%test_name:None,
        },#7
#############
#Typical sync - twice per day, every second day - owncloud clients only - packet sniffer off#
        {
          '%s_testdirstruct'%test_name:"0/1/500000",
          '%s_fullsyncdir'%test_name:"10/100/10000",
        },#8
        {
          '%s_testdirstruct'%test_name:"0/1/50000000",
          '%s_fullsyncdir'%test_name:"10/100/10000",
        },#9
#############
#Stress sync - test many times per day - all clients - packet sniffer on#
#every day, 4am, 8am, 12am, 3pm, 7pm, 12pm.
        {
          '%s_testdirstruct'%test_name:"1/100/100000",
          '%s_rptblocksize'%test_name:None,
          '%s_hashfiles'%test_name:True,
        },#10
        {
          '%s_testdirstruct'%test_name:"10/100/100000",
          '%s_rptblocksize'%test_name:None,
          '%s_hashfiles'%test_name:True,
        },#11
        {
          '%s_testdirstruct'%test_name:"1/5/10000000",
          '%s_rptblocksize'%test_name:None,
          '%s_hashfiles'%test_name:True,
        },#12
        {
          '%s_testdirstruct'%test_name:"1/50/10000000",
          '%s_rptblocksize'%test_name:None,
          '%s_hashfiles'%test_name:True,
        },#13
        {
          '%s_testdirstruct'%test_name:"1/5/100000000",
          '%s_rptblocksize'%test_name:None,
          '%s_hashfiles'%test_name:True,
        },#14
#############
]

@add_worker
def worker0(step): 
    
    exclude_time = eval_excludetime()
    step(1,'Preparation')
    d = make_workdir()
    test_dir,sync_dir_num = prepare_workdir(d)
    
    step(2,'Pre-sync')
    run_ocsync(d,option=exclude_time)
    
    k0,ncorrupt0 = check_workdir(d,test_dir,sync_dir_num)

    step(4,'Add %s files and check if we still have k1+nfiles after resync'%testdirstruct)
    nfiles = create_teststruct(test_dir)

    run_ocsync(d)
    
    k1,ncorrupt1 = check_workdir(d,test_dir,sync_dir_num)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))
    fatal_check((ncorrupt0+ncorrupt1)==0, 'Corrupted files (%s) found'%(ncorrupt0+ncorrupt1))
    logger.info('SUCCESS: %d files found',k1)
        
@add_worker
def worker1(step):
    
    exclude_time = eval_excludetime()
    
    step(2,'Preparation')
    d = make_workdir()
    test_dir,sync_dir_num = get_workdir(d)
    nfiles = eval_teststruct(test_dir)
    step(3,'Pre-sync')
    run_ocsync(d,option=exclude_time)
    k0,ncorrupt0 = check_workdir(d,test_dir,sync_dir_num)

    step(5,'Resync and check files added by worker0')
    run_ocsync(d)

    k1,ncorrupt1 = check_workdir(d,test_dir,sync_dir_num)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))
    fatal_check((ncorrupt0+ncorrupt1)==0, 'Corrupted files (%s) found'%(ncorrupt0+ncorrupt1))

""" TEST UTILITIES """
    
def prepare_workdir(d):
    wdir = os.path.join(d,"0")
    remove_tree(wdir)
    if fullsyncdir!=False:
        conf = fullsyncdir.split('/')
        if len(conf)==3 and int(conf[0])>0:
            for i in range(0, int(conf[0])):
                dir = os.path.join(d,str(i)) 
                if (not (os.path.exists(dir))) or i==0:
                    mkdir(dir)
                    for j in range(int(conf[1])):
                        create_test_file(dir,"%s%s"%(i,j),int(conf[2]))
            return (wdir,int(conf[0]))
        error_check(len(conf)==3,'Improper testdirstruct format, expects dir_n/file_n/file_size')
    reset_owncloud_account()
    reset_rundir()
    mkdir(wdir)
    return (wdir,1)

def get_workdir(d):
    wdir = os.path.join(d,"0")
    remove_tree(wdir)  
    mkdir(wdir)
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

def eval_teststruct(test_dir):
    teststruct = testdirstruct.split('/')
    nfiles = 0
    error_check(len(teststruct)==3,'Improper teststruct format, expects dir_n/file_n/file_size')
    if int(teststruct[0])<1:
        for i in range(int(teststruct[1])):
            nfiles+=1
    else:
        for i in range(int(teststruct[0])):
            dir = os.path.join(test_dir,str(i)) 
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

