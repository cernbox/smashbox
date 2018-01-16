from docx import Document


__doc__ = """ 
This test is to reproduce the read write lock with samba on windows
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *
import logging

logger = logging.getLogger()
nfiles = 4
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

    step(2, 'Create 4 word file and write some content on it')

    process = subprocess.Popen(os.getcwd()[:-3] + "/windows/OfficeUsersSimulation_C.exe nof" +  " " + str(nfiles) +  " "  "crtfls usewd wrkdir " + d)
    run_ocsync(d)

    step(4, 'Open the word file')
    try:
        path = d + "/officeSimulation_word/"
        for filename in os.listdir(path):
            if not filename.endswith("tmp"):
                file = path + filename
                f = open(file, 'rb')
                document = Document(f)
                f.close()
    except Exception as e:
        logger.exception('Error opening the word file to write on it ')


@add_worker
def worker1(step):
    step(1, 'Preparation')
    d = make_workdir()
    run_ocsync(d)
    k0 = count_files(d)
    logger.info('SUCCESS: %d files found', k0)

    step(3, 'Resync and check files added by worker0')

    run_ocsync(d)

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    error_check(k1 - k0 == 1, 'Expecting to have %d files more: see k1=%d k0=%d' % (abs(k1 - 1), k1, k0))
    fatal_check(ncorrupt == 0, 'Corrupted files (%d) found' % ncorrupt)


