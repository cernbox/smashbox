from smashbox.utilities import *
from protocol import quota_check
from smashbox.utilities.hash_files import *
from smashbox.utilities.monitoring import push_to_monitoring

__doc__ = """ 
Creates files to reach the quota limit and then it adds n_exceed_files to exceed the quota limit

This test has been carried out in a simulated environment generated with the uboxed project available on github (https://github.com/cernbox/uboxed).

The goal of this test is to understand the behaviour of cernbox when the eosuser has been setup with limit on quota and number of files and some operations are performed out of this limit

To set the eos quota limit it is needed to run the following commands within uboxed environment:

docker exect -it eos-mgm bash
eos quota set -u "username" -v "max_bytes" -i "max_files" -p /eos/demo/user/ 

For example:
eos quota set -u user9 -v 1GB -i 100 -p /eos/demo/user/ 

"""
# optional fs check before files are uploaded by worker0
fscheck = config.get('nplusone_fscheck', False)

# user quota info
url = oc_webdav_url()
user_info = quota_check(url)
used_bytes=user_info.propfind_response[0][1]['HTTP/1.1 200 OK']['{DAV:}quota-used-bytes']
used_available_bytes=user_info.propfind_response[0][1]['HTTP/1.1 200 OK']['{DAV:}quota-available-bytes']

# set up test main parameters
filesize = int(config.get('quotalimit_filesize',100000000))
nfiles =  int(used_available_bytes) / filesize # compute number of files
n_exceed_files = config.get('quotalimit_n_exceed_files',100)

def adder(step,d):

    step(4,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)


    total_size = 0
    sizes = []

    # compute the file sizes in the set
    for i in range(n_exceed_files):
        size = size2nbytes(filesize)
        sizes.append(size)
        total_size += size

    logger.log(35, "Timestamp %f Exceed files %d TotalSize %d", time.time(), n_exceed_files, total_size)

    # create the test files
    for size in sizes:
        create_hashfile(d, size=size)

    run_ocsync(d)

    step(5,'Get other files from server and check')

    run_ocsync(d)
    (ntot,k1,ncorruptions) = analyse_hashfiles(d)

    k0 = count_files(d)
    error_check(k1-k0==2*nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))
    error_check(ncorruptions==0,'After synch %d corrupted files found'%(ncorruptions))

    logger.info('SUCCESS: %d files found',k1)

@add_worker
def worker0(step):
    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1, 'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    step(2, 'Add %s files and check if we still have k1+nfiles after resync' % nfiles)

    total_size = 0
    sizes = []

    # compute the file sizes in the set
    for i in range(nfiles):
        size = size2nbytes(filesize)
        sizes.append(size)
        total_size += size

    time0 = time.time()

    logger.log(35, "Timestamp %f Files %d TotalSize %d", time.time(), nfiles, total_size)

    # create the test files
    for size in sizes:
        create_hashfile(d, size=size)

    if fscheck:
        # drop the caches (must be running as root on Linux)
        runcmd('echo 3 > /proc/sys/vm/drop_caches')

        ncorrupt = analyse_hashfiles(d)[2]
        fatal_check(ncorrupt == 0, 'Corrupted files ON THE FILESYSTEM (%s) found' % ncorrupt)

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(d)[2]

    k1 = count_files(d)

    error_check(k1 - k0 == nfiles, 'Expecting to have %d files more: see k1=%d k0=%d' % (nfiles, k1, k0))

    fatal_check(ncorrupt == 0, 'Corrupted files (%s) found' % ncorrupt)

    logger.info('SUCCESS: %d files found', k1)

    # Add files to exceed eos quota
    adder(step,d)

    step(6, "Final report")

    time1 = time.time()
    push_to_monitoring("cernbox.cboxsls.nplusone.nfiles", nfiles)
    push_to_monitoring("cernbox.cboxsls.nplusone.total_size", total_size)
    push_to_monitoring("cernbox.cboxsls.nplusone.elapsed", time1 - time0)
    push_to_monitoring("cernbox.cboxsls.nplusone.total_size", total_size)
    push_to_monitoring("cernbox.cboxsls.nplusone.transfer_rate", total_size / (time1 - time0))
    push_to_monitoring("cernbox.cboxsls.nplusone.worker0.synced_files", k1 - k0)


@add_worker
def worker1(step):
    step(1, 'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    step(3, 'Resync and check files added by worker0')

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    push_to_monitoring("cernbox.cboxsls.nplusone.worker1.synced_files", k1 - k0)
    push_to_monitoring("cernbox.cboxsls.nplusone.worker1.cor", ncorrupt)

    error_check(k1 - k0 == nfiles, 'Expecting to have %d files more: see k1=%d k0=%d' % (nfiles, k1, k0))

    fatal_check(ncorrupt == 0, 'Corrupted files (%d) found' % ncorrupt)  # Massimo 12-APR

