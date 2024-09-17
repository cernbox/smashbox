import os
import time
import tempfile
import shutil
import hashlib

__doc__ = """ Add nfiles to a directory and check consistency.
"""

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

nfiles = int(config.get('fs_nplusone_nfiles',10))
filesize = config.get('fs_nplusone_filesize',1000)
local_path = config.get('local_path',"")
rsync_path = config.get('rsync_path',"")
local_written_file = os.path.join(local_path,'tests')
rsync_written_file = os.path.join(rsync_path,'tests')
local_touch_file = os.path.join(local_path,'touch')
rsync_touch_file = os.path.join(rsync_path,'touch')

if type(filesize) is type(''):
    filesize = eval(filesize)

testsets = [
        { 'fs_nplusone_filesize': 1000,
          'fs_nplusone_nfiles':100
        },

        { 'fs_nplusone_filesize': OWNCLOUD_CHUNK_SIZE(0.3),
          'fs_nplusone_nfiles':10
        },

        { 'fs_nplusone_filesize': OWNCLOUD_CHUNK_SIZE(1.3),
          'fs_nplusone_nfiles':2
        },

        { 'fs_nplusone_filesize': OWNCLOUD_CHUNK_SIZE(3.5),
          'fs_nplusone_nfiles':1
        },

        { 'fs_nplusone_filesize': (3.5,1.37), # standard file distribution: 10^(3.5) Bytes
          'fs_nplusone_nfiles':10
        },

]

@add_worker
def worker0(step):

    step(1,'Creation')
    
    if os.path.isdir(local_written_file):
        shutil.rmtree(local_written_file)
        
    os.mkdir(local_written_file)
    print(local_written_file)

    if os.path.isdir(rsync_written_file):
        shutil.rmtree(rsync_written_file)

    os.mkdir(rsync_written_file)

    if os.path.isdir(local_touch_file):
        shutil.rmtree(local_touch_file)

    os.mkdir(local_touch_file)
    
    if os.path.isdir(rsync_touch_file):
        shutil.rmtree(rsync_touch_file)

    os.mkdir(rsync_touch_file)
        
    for i in range(nfiles):
      create_hashfile(local_written_file,size=filesize)

    k0 = count_files(local_written_file)

    #step(2,'touch remote dir')

    step(2, 'new file')

    if os.path.isdir(local_touch_file):
        shutil.rmtree(local_touch_file)

    os.mkdir(local_touch_file)
    
    for i in range(1):
        #create_hashfile(rsync_touch_file,size=0)
        create_hashfile(local_touch_file,size=filesize)
    

    my_file = os.listdir(local_touch_file)
    print local_touch_file

    os.mknod(rsync_touch_file+'/'+my_file[0])

    step(3,'Copy')

    #my_file = create_hashfile(local_touch_file,size=filesize)

    #for i in range (1):
        #datablock = 'qwerty'
        #datablock=(os.urandom(1))
        #my_file.write(datablock)
        #my_file
    #my_file.close
    #print (my_file)

    #hashfile1 = hashlib.md5(open('/tmp/rsync/touch/touchfile','rb')).hexdigest()
    #hashfile1 = os.system('md5sum /tmp/rsync/touch/d41d8cd98f00b204e9800998ecf8427e')
    #print(hashfile1)
    #os.rename('/tmp/rsync/touch/touchfile', '/tmp/rsync/touch/'+hashfile1)
    
    os.system('cp {source} {dest}'.format(source=local_touch_file+'/'+my_file[0], dest=rsync_touch_file+'/'+my_file[0]))
    
    #hashfile1 = hashlib.md5(open(d41d8cd98f00b204e9800998ecf8427e,'rb')).hexdigest()

    #os.rename('{source} {dest}'.format(source=rsync_touch_file, dest=rsync_touch_file+hashfile1))
    
@add_worker
def worker1(step):

    step(1,'rsync')

    for i in range(nfiles):
        cmd = ('rsync -av --progress {source} {dest}'.format(source=local_written_file ,dest=rsync_path))
        print (cmd)

        os.system(cmd)

    step(2,'rsync final')

    for i in range(nfiles):
        cmd = ('rsync -av --progress {source} {dest}'.format(source=local_written_file ,dest=rsync_path))
        print (cmd)

        os.system(cmd)

@add_worker
def worker2(step):

    step(4,'checksum')

    ncorrupt = analyse_hashfiles('{dir}'.format(dir=rsync_written_file))[2]

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    step(4,'checksum touch')
    
    ncorrupt = analyse_hashfiles('{dir}'.format(dir=rsync_touch_file))[2]

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)
