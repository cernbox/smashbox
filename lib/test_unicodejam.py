import os
import time
import tempfile


__doc__ = """ Add 1 (n) files to a directory (1 client) and check consistency across synch (2 clients).
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

nfiles = 10

def removeunicodejam(localdir):
    import glob
    fl = glob.glob(localdir+os.sep+'*')
    for f in fl:
        os.remove(f)
    return

def checkunicodejam(localdir):
    import glob
    fl = glob.glob(localdir+os.sep+'*')

    ngood = 0 
    nbad = 0

    for f in fl:
        #print 'Checking:',f
        fh = file(f)
        a = localdir+os.sep+fh.read()
        if a!=f: 
            logger.error('%s',f)
            logger.error('%s',a.decode("UTF-8"))
            fh.close()
            nbad += 1
        else:
            ngood += 1

    return(ngood,nbad)
    
def createunicodejam(localdir):
    import random
    forbidden = "/"
    nchar = int(random.uniform(1,100))
    raw = u""
    for i in range(nchar):
        j = int( 1 + random.triangular(0,10,100)*(1+random.uniform(0,1)))
        #j = int(random.uniform(97,122)) # small caps
        cc = unichr(j)
        if cc in forbidden: continue
        raw+=cc

    filename = raw

    if len(filename)>0:
        ff = localdir+os.sep+filename
        #print 'Preparing:',ff
        fh = file(ff,'w')
        fh.write(filename.encode("UTF-8"))
        fh.close
    else:
        'No file %s created (zero length)',ff

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
    if k0>0:
        os.system('rm '+d+os.sep+'*')
        run_ocsync(d)
        k0 = count_files(d)
    assert k0==0,'Cannot cleanup the directory %s' % d

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    for i in range(nfiles):
        logger.info('*** Creating file: %d',i)
        createunicodejam(d)

    run_ocsync(d)

    (ngood,nbad) = checkunicodejam(d)

    error_check(ngood==nfiles,'Not all files are OK! good=%d, bad=%d, expected=%d'%(ngood,nbad,nfiles))
    error_check(nbad==0,'After synch corrupted files found good=%d, bad%d, expected=%d'%(ngood,nbad,nfiles))

    if ngood==nfiles and nbad==0: logger.info('SUCCESS: %d files found',ngood)

    step(3,'Do nothing')

        
@add_worker
def worker1(step):

    step(1,'Preparation')
    d = make_workdir()

    step(2,'Do nothing')

    step(3,'Resync and check files added by worker0')

    run_ocsync(d)

    (ngood,nbad) = checkunicodejam(d)

    error_check(ngood==nfiles,'Not all files are OK! good=%d, bad=%d, expected=%d'%(ngood,nbad,nfiles))
    error_check(nbad==0,'After synch corrupted files found: good=%d, bad=%d, expected=%d'%(ngood,nbad,nfiles))

    if ngood==nfiles and nbad==0: logger.info('SUCCESS: %d files found',ngood)






