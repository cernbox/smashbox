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
    fl = glob.glob(unicode(localdir+os.sep+'*'))

    ngood = 0 
    nbad = 0

    for f in fl:
        logger.debug('Checking: %s',f)
        fh = file(f)
        a = localdir+os.sep+fh.read()
        a = a.decode("UTF-8")

        if a!=f: 
            logger.error('FILELEN: %d',len(f))
            logger.error('FILE   : %s',f)
            logger.error('CONTENT: %s',a)
            logger.error('CONTLEN: %d',len(a))

            logger.error("FILE    BYTES: %s %d",repr(f),len(repr(f)))
            logger.error("CONTENT BYTES: %s %d",repr(a),len(repr(a)))
            fh.close()
            nbad += 1
        else:
            ngood += 1

    return(ngood,nbad)

import sys

##
# various unicode random generators which probe subsets of unicode space
# 
# 
import random

def g_massimo():
    return int( 1 + random.triangular(0,10,100)*(1+random.uniform(0,1)))  # this gives only ASCII ?

def g_all_unicode():
    return int(random.uniform(97,sys.maxunicode))   # with this I manage to "break" owncloud server 5.0.14a  --> I needed to manually delete entries from oc_filecache

def g_plane0_unicode():
    return int(random.uniform(0x80,0xffff)) # unicode plane0 only, non-ascii

def g_plane0_unicode_degressive():
    return int(random.triangular(0x80,0xffff,0x80))   # unicode plane0 only, non-ascii

def g_plane0_reduced():
    return int(random.uniform(0x80,0x1000))   # unicode plane0 only, non-ascii, first few pages only...

##


def createunicodejam(localdir):

    forbidden = "/"
    nchar = int(random.uniform(1,50))
    raw = u""
    for i in range(nchar):

        j = g_plane0_reduced()

        cc = unichr(j)
        if cc in forbidden: continue
        raw+=cc

    filename = raw

    assert( len(filename) > 0)

    ff = localdir+os.sep+filename
    #print 'Preparing:',ff
    try:
        fh = file(ff,'w')
        fh.write(filename.encode("UTF-8"))
        fh.close
    except Exception,x:
        logger.warning('cannot create file: %s',x)


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






