
__doc__ = """

This test is testing that if the data-fingerprint changes because of a backup restoration
we do not loose the newer file that were on the server
[]

"""

from smashbox.utilities import *
import subprocess
import glob


@add_worker
def workerA(step):
    if compare_client_version('2.3.0', '<'):
        logger.warning('Skipping test, because the client version is known to behave incorrectly')
        return

    #cleanup remote and local test environment - this should be run once by one worker only
    reset_owncloud_account()
    reset_rundir()

    

    step(0,'create initial content and sync')

    syncdir = make_workdir()
    folder1 = make_workdir(os.path.join(syncdir, 'folder1'))
    createfile(os.path.join(folder1, 'file.txt'), '0', count=1000, bs=50)
    createfile(os.path.join(syncdir, 'file1.txt'), '0', count=1000, bs=50)
    createfile(os.path.join(syncdir, 'file2.txt'), '0', count=1000, bs=50)
    createfile(os.path.join(syncdir, 'file3.txt'), '0', count=1000, bs=50)

    run_ocsync(syncdir)

    
    step(1,'simulate a backup restored by faking an old state')
    # it is as if file1.txt was newer and thus not present in the backup
    remove_file(os.path.join(syncdir, 'file1.txt'))
    
    # folder1 was not present on the backup
    remove_tree(os.path.join(syncdir, 'folder1'))
    
    # file2.txt is replaced by an "older" file
    createfile(os.path.join(syncdir, 'file2.txt'), '1', count=1000, bs=40)

    step(2, 'upload an the fake old state state')
    run_ocsync(syncdir)
    

@add_worker
def workerB(step):

    if compare_client_version('2.3.0', '<'):
        logger.warning('Skipping test, because the client version is known to behave incorrectly')
        return

    step(1,'sync the initial content')

    syncdir = make_workdir()
    run_ocsync(syncdir)
    
    step(3,'simulate a backup by altering the data-fingerprint')
    
    #Since i can't change the data finferprint on the server, i change it on the client's database
    subprocess.check_output(["sqlite3" , os.path.join(syncdir, ".csync_journal.db"),
        "DELETE FROM datafingerprint; INSERT INTO datafingerprint (fingerprint) VALUES('1234');"])

    run_ocsync(syncdir)

    error_check(os.path.isdir(os.path.join(syncdir, 'folder1')), 
                "folder1 should have been restored ")
    
    error_check(os.path.exists(os.path.join(syncdir, 'folder1/file.txt')), 
                "folder1/file.txt should have been restored ")

    conflict_files = get_conflict_files(syncdir)
    error_check(len(conflict_files) == 1,
                "file2 should have been backed up as a conflict ")
    
