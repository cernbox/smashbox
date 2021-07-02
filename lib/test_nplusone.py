import os
import time
import socket
import tempfile
from ConfigParser import NoOptionError, NoSectionError

__doc__ = """ Add nfiles to a directory and check consistency.
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.utilities.monitoring import push_to_monitoring

nfiles = int(config.get('nplusone_nfiles',10))
filesize = config.get('nplusone_filesize',1000)

hostname = socket.gethostname()
hostname = str.split(hostname, '.cern.ch')[0]

try:
    instance_name = config['instance_name']
except AttributeError:
    instance_name = None

if instance_name is None:
	source = 'cernbox.%s.nplusone' % hostname
else:
	source = 'cernbox.%s.%s.nplusone' % (hostname,instance_name)


# optional fs check before files are uploaded by worker0
fscheck = config.get('nplusone_fscheck',False)

if type(filesize) is type(''):
    filesize = eval(filesize)

# True => use new webdav endpoint (dav/files)
# False => use old webdav endpoint (webdav)
use_new_dav_endpoint = bool(config.get('use_new_dav_endpoint',True))

testsets = [
        { 'nplusone_filesize': 1000, 
          'nplusone_nfiles':100
        },

        { 'nplusone_filesize': OWNCLOUD_CHUNK_SIZE(0.3), 
          'nplusone_nfiles':10
        },

        { 'nplusone_filesize': OWNCLOUD_CHUNK_SIZE(1.3), 
          'nplusone_nfiles':2
        },

        { 'nplusone_filesize': OWNCLOUD_CHUNK_SIZE(3.5), 
          'nplusone_nfiles':1
        },

        { 'nplusone_filesize': (3.5,1.37), # standard file distribution: 10^(3.5) Bytes
          'nplusone_nfiles':10
        },

]

def finish_if_not_capable():
    # Finish the test if some of the prerequisites for this test are not satisfied
    if compare_oc_version('10.0', '<') and use_new_dav_endpoint == True:
        #Dont test for <= 9.1 with new endpoint, since it is not supported
        logger.warn("Skipping test since webdav endpoint is not capable for this server version")
        return True
    return False

@add_worker
def worker0(step):
    if finish_if_not_capable():
        return

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)
    k0 = count_files(d)

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    total_size=0
    sizes=[]

    # compute the file sizes in the set
    for i in range(nfiles):
        size=size2nbytes(filesize)
        sizes.append(size)
        total_size+=size

    time0=time.time()

    logger.log(35,"Timestamp %f Files %d TotalSize %d",time.time(),nfiles,total_size)

    # create the test files
    for size in sizes:
        create_hashfile(d,size=size)

    if fscheck:
        # drop the caches (must be running as root on Linux)
        runcmd('echo 3 > /proc/sys/vm/drop_caches')
        
        ncorrupt = analyse_hashfiles(d)[2]
        fatal_check(ncorrupt==0, 'Corrupted files ON THE FILESYSTEM (%s) found'%ncorrupt)

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    ncorrupt = analyse_hashfiles(d)[2]
    
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    logger.info('SUCCESS: %d files found',k1)

    step(4,"Final report")

    time1 = time.time()

    push_to_monitoring("%s.nfiles" % source,nfiles)
    push_to_monitoring("%s.total_size" % source,total_size)
    push_to_monitoring("%s.elapsed" % source,time1-time0)
    push_to_monitoring("%s.total_size" % source,total_size)
    push_to_monitoring("%s.transfer_rate" % source,total_size/(time1-time0))
    push_to_monitoring("%s.worker0.synced_files" % source,k1-k0)
    push_to_monitoring("%s.norm_synced_files" % source,float((k1-k0)/nfiles))


        
@add_worker
def worker1(step):
    if finish_if_not_capable():
        return

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)
    k0 = count_files(d)

    step(3,'Resync and check files added by worker0')

    time0=time.time()
    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)
    time1=time.time()

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    push_to_monitoring("%s.worker1.synced_files" % source,k1-k0)
    push_to_monitoring("%s.worker1.cor" % source,ncorrupt)
                       
    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%d) found'%ncorrupt) #Massimo 12-APR

    step(4,"Final report")
    push_to_monitoring("%s.elapsed" % source,time1-time0)



