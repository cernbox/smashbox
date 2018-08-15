from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from os import listdir
from os.path import isfile, join
from smashbox.utilities.monitoring import push_to_monitoring

import sys,os,os.path,random

username = config.get('reva_tests_username', 'foo')
password = config.get('reva_tests_password', 'bar')
revad_address = config.get('reva_tests_revad_address', 'localhost:9999')
reva_cli = config.get('reva_tests_reva_cli_binary', '/usr/local/bin/reva-cli')
blocksize = int(config.get('reva_tests_revad_blocksize', 3*1024*1024)) # default 3MiB
remainder = int(config.get('reva_tests_remainder', 1024*3)) # default 3kib
revad_target_folder = config.get('reva_tests_revad_target_folder', '/home/')

# create file distribution with (i * blocksize) + remainder
size_distribution = []
for i in range(0, 10):
    size_distribution.append(i*blocksize)
    size_distribution.append(i*blocksize + remainder)

nfiles = len(size_distribution)
total_size = sum(size_distribution)

# Check if reva_cli binary exists
ok = os.path.isfile(reva_cli)
if not ok:
    logger.error("reva-cli tool not found at %s" % (reva_cli))
    sys.exit(1)


@add_worker
def main(step):
    t0 = time.time()
    print "Run options: nfiles=%d revad_address=%s username=%s password=%s blocksize=%d" % (nfiles, revad_address, username, "xxxx", blocksize)

    # create work directory
    d = make_workdir()
    e = d + '-download' # work directory for downloads
    os.mkdir(e, 0755)
    
    remote_folder = join(revad_target_folder, os.path.basename(os.path.dirname(d)))
    print "d=%s e=%s remote_folder=%s" % (d, e, remote_folder)

    # create sample files from the size_distribution
    create_sample_files(d)
    k0 = count_files(d)
    print "Creating sample files succeded: numfiles=%d" % (k0)

    # get all the hash_files created
    hash_files = get_hash_files(d)

    # authenticate to the revad daemon
    reva_authenticate()
# create revad_target_folder in the revad daemon
    reva_create_target_folder(remote_folder)

    # upload the hash files to the revad daemon
    reva_upload_sample_files(remote_folder, hash_files)

    # download the hash files to the original location
    reva_download_sample_files(remote_folder, e, hash_files) 
    k1 = count_files(e)
    print "Downloading sample files succeded: numfiles=%d" % (k1)
    
    error_check(k1-k0==0,'Expected to have the same number of files: nfiles=%d sampled=%d downloaded=%d'%(nfiles,k0,k1))


    # verify downloaded sample files for corruptions
    ncorrupt = verify_sample_files(e)[2]
    fatal_check(ncorrupt==0, 'Corrupted files (%d) found' % (ncorrupt))

    # clean local workdir and revad_target_folder
    # assuming that verify_sample_files(d) will abort
    # if corruption happened
    clean_run(remote_folder)

    t1 = time.time()
    push_to_monitoring("cernbox.cboxsls.revad_corruption.nfiles", nfiles)
    push_to_monitoring("cernbox.cboxsls.revad_corruption.total_size", total_size)
    push_to_monitoring("cernbox.cboxsls.revad_corruption.elapsed", t1-t0)
    push_to_monitoring("cernbox.cboxsls.revad_corruption.transfer_rate", total_size/(t1-t0))
    push_to_monitoring("cernbox.cboxsls.revad_corruption.downloaded_files", k1)

# create_sample_files create the sample files
def create_sample_files(d):
    print "Creating sample files ..."

    # create sample files inside folder
    for size in size_distribution:
        print "Creating sample file: size=%d bs=%d" % (size, blocksize)
        create_hashfile(d, size=size, bs=blocksize)



def get_hash_files(d):
    hash_files = [join(d, f) for f in listdir(d) if isfile(join(d, f))]
    return hash_files

def reva_authenticate():
    uri = "tcp://%s:%s@%s" % (username, password, revad_address)
    cmd = "%s login %s" % (reva_cli, uri)
    print "REVA auth: cmd=%s" % (cmd)
    runcmd(cmd)

def reva_create_target_folder(target_folder):
    # missing mkdir on the reva-cli, xrdcopy will create dir for us
    pass


def reva_upload_sample_files(remote_folder, hash_files):
    print "Uploading sample files ..."
    # upload using reva-cli to remote server
    for f in hash_files:
         upload(remote_folder, f)

# upload uploads a file to revad
def upload(remote_folder, fn):
    target_fn = join(remote_folder, os.path.basename(fn))
    cmd = "%s storage upload %s %s" % (reva_cli, target_fn, fn)
    print "REVA upload: cmd=%s" % (cmd)
    runcmd(cmd)

def reva_download_sample_files(remote_folder, e, hash_files):
    print "Downloading sample files ..."
    # download using reva-cli to local disk
    for f in hash_files:
         download(remote_folder, e, f)

# download downloads a file to revad
def download(remote_folder, e, fn):
    remote_fn = join(remote_folder, os.path.basename(fn))
    local_fn = join(e, os.path.basename(fn))
    cmd = "%s storage download %s %s" % (reva_cli, remote_fn, local_fn)
    print "REVA download: cmd=%s" % (cmd)
    runcmd(cmd)

def verify_sample_files(d):
    print "Verifying uploaded files ..."
    # verify that the checksums of the downloaded files
    # matches the one of the sample file
    return analyse_hashfiles(d)

def clean_run(remote_folder):
    cmd = "%s storage delete %s" % (reva_cli, remote_folder)
    print "REVA clean: cmd=%s" % (cmd)
    runcmd(cmd)
    

