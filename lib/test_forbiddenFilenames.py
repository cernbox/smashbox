import os
import time
import tempfile


__doc__ = """ Add invalid named files to a directory and check consistency. """

from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.utilities.monitoring import push_to_monitoring

forbidden_charsets = {
		'backslash' : '\\',
                 'colon' : ':',
                 'questionmark' : '?',
                 'asterisk' : '*',
                 'doublequote' : '"',
                 'greater' : '>',
                 'smaller' : '<',
                 'pipe'    : '|'
}

nfiles = len(forbidden_charsets)


do_not_report_as_failure()


@add_worker
def worker0(step):

    # do not cleanup server files from previous run
    reset_owncloud_account()

    # cleanup all local files for the test
    reset_rundir()

    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)



    step(2,'Dir %s has %d files. Add %d files then resync and check if we still have %d files'%(d,k0,nfiles,k0+nfiles))
    logger.log(35,"Timestamp %f Files %d",time.time(),nfiles)

    for c in forbidden_charsets:
        print d+'/'+forbidden_charsets[c]
        createfile(d+'/'+forbidden_charsets[c], 'a', 1, 3)
#    print '/\\'
#    print '/:'
#    print '/?'
#    print '/*'
#    print '/"'
#    print '/>'
#    print '/<'
#    print '/|'

#    createfile(d+'/\\', 'a', 1, 3)
#    createfile(d+'/:', 'a', 1, 3)
#    createfile(d+'/?', 'a', 1, 3)
#    createfile(d+'/*', 'a', 1, 3)
#    createfile(d+'/"', 'a', 1, 3)
#    createfile(d+'/>', 'a', 1, 3)
#    createfile(d+'/<', 'a', 1, 3)
#    createfile(d+'/|', 'a', 1, 3)
#    createfile(d+'/newFile', 'a', 1, 3)

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(d)[2]
    
    k1 = count_files(d)

    error_check(k0+nfiles==k1+nfiles,'Expecting to have %d files in %s - found instead %d'%(k0+nfiles,d,k1+nfiles))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    logger.info('SUCCESS: %d files found',k1)


@add_worker
def worker1(step):
    step(1,'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)

    step(3,'Resync and check files added by worker0')

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)
                       
    error_check(k1==0,'Expecting to have 0 files, due to illegal filenames: see k1=%d '%(k1))

    fatal_check(ncorrupt==0, 'Corrupted files (%d) found'%ncorrupt)


