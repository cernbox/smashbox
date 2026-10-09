
from smashbox.utilities import *

# utilities to create and process self-describing hashfiles
# a hashfile encodes its content checksum in its name

# the name of a hashfile may be specified using a template string (filemask) where {md5} string represents the content checksum
# for example: "test_{md5}.dat" 

# hashfile size may be specified as
#  - number of bytes (int)
#  - a gaussian distribution (mean,sigma)

config.hashfile_size = (3.5,1.37) # standard file distribution: 10^(3.5) Bytes
config.hashfile_bigsize = (5,1.37) # big file distribution

#if defined, the file size distribution will be cut off at hashfile_maxsize
config.hashfile_maxsize = 5*1000*1000*1000

# these are ignored files which are normally not synced

config.ignored_files = ['.csync_journal.db', '.csync_journal.db-wal', '.csync_journal.db-shm']

# control memory usage of functions reading/generating files
BLOCK_SIZE = 1024*1024

import os
import fnmatch
from typing import Any

# a file size specification: number of bytes or a (mean,sigma) gaussian distribution of log10(nbytes)
SizeSpec = int | str | tuple[float, float]


def get_files(wdir: str, filemask: str | None = None) -> set[str]:
    fl = [f for f in os.listdir(wdir) if os.path.isfile(os.path.join(wdir,f))]
    # if filemask defined then filter names out accordingly
    if filemask:
        fl = fnmatch.filter(fl, filemask.replace('{md5}', '*'))
    sync_journal_file = fnmatch.filter(fl, '.*sync_*.db')
    fl = set(fl) - set(config.ignored_files) - set(sync_journal_file)
    return fl


def count_files(wdir: str, filemask: str | None = None) -> int:
    fl = get_files(wdir, filemask)
    nf = len(fl)
    logger.info('%s: %d files found', wdir, nf)
    return nf


def size2nbytes(size: SizeSpec) -> int:
    """ Return the number of bytes from the size specification (size may be a distribution or nbytes directly).
    """
    
    import random, math

    def make_distrib(size: Any) -> int:
        xxx = random.gauss(size[0],size[1])
        nbytes = int(math.pow(10,xxx))
        if nbytes<10:nbytes=10
        if config.hashfile_maxsize and nbytes>config.hashfile_maxsize:
            nbytes=config.hashfile_maxsize
        return nbytes

    try:
        return int(size) # type: ignore[arg-type] # a (mean,sigma) distribution raises TypeError
    except TypeError:
        return make_distrib(size)
    except ValueError:
        return make_distrib(size)        

def create_hashfile(wdir: str, filemask: str | None = None, size: SizeSpec | None = None, bs: int | None = None, slow_write: float | None = None) -> str:
    """ Create a random file in wdir.The md5 checksum is placed in the filname name according to filemask: {md5} string in the filemask is replaced by the file checksum.
    By default the filemask == {md5} so the filename consists of only the checksum.

    The function will use max BLOCK_SIZE memory. Below BLOCK_SIZE the file is fully random. For larger files the BLOCK_SIZE bytes are replicated.

    The default BLOCK_SIZE may be changed with the bs argument.
    Optional slow_write may specify the delay in seconds between writing blocks.

    Return name of the create file.

    """
    return create_hashfile2(wdir,filemask,size,bs,slow_write)[0]

def create_hashfile2(wdir: str, filemask: str | None = None, size: SizeSpec | None = None, bs: int | None = None, slow_write: float | None = None) -> tuple[str, str]:
    """ Same as create_hashfile but return (filename,md5sum).
    """

    import hashlib
    import random

    if size is None:
        size = config.hashfile_size

    nbytes = size2nbytes(size)

    if not bs:
        bs = BLOCK_SIZE

    nblocks = nbytes//bs
    nr = nbytes%bs

    assert nblocks*bs+nr==nbytes,'Chunking error!'

    time.sleep(0.1)

    # Prepare the building blocks
    block_data = os.urandom(bs) # Repeated nblocks times
    block_data_r = os.urandom(nr)       # Only once

    #block_data = str(time.time()) + 'a'*bs;
    #block_data_r = 'a'*nr; 

    #time.sleep(0.1)
    #block_data =  str(time.time()) + ":".join(["%09s"%n for n in range(90000)]) #str([str(n)+':' for n in range(10000)])
    #block_data_r = ""

    # Precompute the checksum - we do it separately before writing the file to avoid the file rename
    md5 = hashlib.md5()
    for kb in range(nblocks):
        md5.update(block_data)
    md5.update(block_data_r)

    if filemask is None:
        filemask = "{md5}"        


    fn = os.path.join(wdir,filemask.replace('{md5}',md5.hexdigest()))

    f = open(fn,'wb')

    # write data blocks
    for i in range(nblocks):
        if slow_write:
            logger.info('slow_write=%s %d %s',slow_write,i,fn)
            time.sleep(slow_write)
        f.write(block_data)
        if slow_write:
            f.flush()

    f.write(block_data_r)
    f.close()

    logger.info("Written hash file %s, nbytes=%d",fn,nbytes)
    
    return fn,md5.hexdigest()

def analyse_hashfiles(wdir: str, filemask: str | None = None) -> tuple[int, int, int]:

    """ Analyse files in wdir for md5 correctness.

    If filemask is not provided, analyze all possible files found in wdir.

    If filemask is provided, analyze only the files which match the filemask pattern ('{md5}' gets replaced by '*')
    
    """
    
    import glob
    import hashlib

    ncorrupt = 0
    nfiles = 0
    nanalysed = 0

    import re

    if filemask is None:
        #match any names containing a block of 32 characters from hex character set
        md5_regexp = r'\S*([a-fA-F0-9]{32,32})\S*'
    else:
        # re.escape in order to allow *? in the filemask
        # a block of 32 characters from hex character set comes in place of {md5} token
        md5_regexp = re.escape(filemask).replace(r'\{md5\}','([a-fA-F0-9]{32,32})')

    md5_pattern = re.compile(md5_regexp)

    if filemask is None:
        glob_pattern = "*"
    else:
        glob_pattern = filemask.replace('{md5}','*')

    
    for fn in glob.glob(os.path.normpath(os.path.join(wdir,glob_pattern))): 

        if not os.path.isfile(fn): 
            continue # Go for files!

        nfiles += 1

        m = md5_pattern.match(os.path.basename(fn))

        if m:
            md5_name = m.group(1)
        else:
            continue # cannot extract md5 from filename

        nanalysed += 1

        md5_data = md5sum(fn)
        
        if md5_data!=md5_name:
            osize = os.path.getsize(fn)
            error_check(False, 'Corrupted file? %s:  md5 expected %s computed %s (observed size=%s)'%(fn,repr(md5_name),repr(md5_data),osize))
            
            ncorrupt += 1

    logger.info("Found %d files in %s: analysed %d, corrupted %d",nfiles,wdir,nanalysed,ncorrupt)
    
    return (nfiles,nanalysed,ncorrupt)

def md5sum(fn: str) -> str: # type: ignore[no-redef] # shadows smashbox.utilities.md5sum (which calls this one)
    import hashlib
    md5 = hashlib.md5()
        
    f = open(fn,'rb')
    
    while True:
        chunk = f.read(BLOCK_SIZE)
        if not chunk: break
        md5.update(chunk)

    f.close()
        
    return md5.hexdigest()

def adler32(fn: str) -> str:
    import zlib
    v = 1
    f = open(fn,'rb')

    while True:
        chunk = f.read(BLOCK_SIZE)
        if not chunk: break
        v = zlib.adler32(chunk,v)
            
    f.close()

    return '%x' % (v & 0xffffffff)

# TO BE REVIEWED...

def create_hashfile_big(wdir: str, size: SizeSpec | None = None) -> str:
    if size is None:
        size = config.hashfile_bigsize
    return create_random_file(wdir,size=size) # type: ignore[name-defined] # FIXME: pre-existing bug, create_random_file is not defined

def cleanup_dir(wdir: str) -> None:
    import hashlib
    import re
    conflict=re.compile(r"test_conflict-\d\d\d\d\d\d\d\d-\d\d\d\d\d\d.dat") # test.dat conflict
    fl = os.listdir(wdir)
    for f in fl:
        md50 = os.path.basename(f)
        if md50=='.csync_journal.db':
          continue
        md51 = md5sum(wdir+'/'+f)
        if md50==md51 or f=='test.dat' or conflict.match(f) or 'tobedeleted_' in f:
          os.unlink(wdir+'/'+f)
    return

def detect_conflict(wdir: str) -> int | str: # type: ignore[return] # (the sys.exit() branch)
    import glob
    import hashlib
    ll = glob.glob(wdir+'/test_conflict*.dat')
    nl = len(ll)
    if nl==0:
        return 0
    elif nl>1:
        print('+++ Severe error %d conflict files found!' % nl)
        sys.exit(1) # type: ignore[name-defined] # FIXME: pre-existing bug, sys is not imported
    else:
        bl = os.path.basename(ll[0])
        f1 = open(ll[0],'rb')
        f2 = open(wdir+'/test.dat','rb')
        a1 = f1.read()
        a2 = f2.read()
        f1.close()
        f2.close()
        l1 = len(a1)
        l2 = len(a2)
        md51 = hashlib.md5(a1).hexdigest()
        md52 = hashlib.md5(a2).hexdigest()
        if (md51==md52): 
            print('Conflict file identical to original')
            return 1
        print('File %s size: %d, test.dat size: %d' % (bl,l1,l2))
        minl = 10
        if l1<minl: minl=l1
        if l2<minl: minl=l2
        print('bl: %s...' % a1[:minl].decode('utf-8','replace'))
        print('test.dat: %s...' % a2[:minl].decode('utf-8','replace'))
        return ll[0]


if __name__ == "__main__":
   import logging
   logging.basicConfig()
   logger=logging.getLogger()

   import smashbox.utilities
   smashbox.utilities.logger = logger

   mkdir("TEST-hashfile")

   print(create_hashfile("TEST-hashfile","mytest_{md5}.jpg",size=1000000))
   print(create_hashfile("TEST-hashfile","mytest_{md5}.jpg"))
   print(create_hashfile("TEST-hashfile","mytest_{md5}.jpg"))

   print(analyse_hashfiles("TEST-hashfile","mytest_{md5}.jpg"))
   print(analyse_hashfiles("TEST-hashfile"))
