
__doc__ = """

This test is testing that moving files server multiple do not get uploaded
too much. Even if the files are moved when the sync is running.
[https://github.com/owncloud/client/issues/4370]

"""

from smashbox.utilities import *
import subprocess

nfiles = 20
TEST_FILES = ['test%02d.dat'%i for i in range(nfiles)]

def getFileId(syncdir, fileName):
    return subprocess.check_output(["sqlite3" , syncdir + "/.csync_journal.db",
        "select fileid from metadata where path = \"" + fileName + "\""])

@add_worker
def workerA(step):
    if compare_client_version('2.1.0', '<='):
        logger.warning('Skipping test, because the client version is known to behave incorrectly')
        return

    #cleanup remote and local test environment - this should be run once by one worker only
    reset_owncloud_account()
    reset_rundir()

    syncdir = make_workdir("workdir")
    d1 = os.path.join(syncdir,"dir1")
    d2 = os.path.join(syncdir,"dir2")
    d_final = os.path.join(syncdir,"dirFinal")

    step(0,'create initial content and sync')


    # create a folder and some files in it
    mkdir(d1)

    for f in TEST_FILES:
        fn = os.path.join(d1,f)
        createfile(fn,'0',count=1000,bs=1000)

    run_ocsync(syncdir)

    fileIds = list(map((lambda f:getFileId(syncdir, 'dir1/' + f)), TEST_FILES))

    step(1,'move the folder')

    mkdir(d2)
    mv(d1+"/*",d2)

    step(2, 'sync')
    run_ocsync(syncdir)

    step(3,'final sync')

    run_ocsync(syncdir)

    final_fileIds = list(map((lambda f:getFileId(syncdir, 'dirFinal/' + f)), TEST_FILES))

    #The file ids needs to stay the same for every files, since they only got moved and not re-uploaded
    error_check(fileIds == final_fileIds, "File id differ (%s != %s)" % (fileIds, final_fileIds))


@add_worker
def workerB(step):

    if compare_client_version('2.1.0', '<='):
        logger.warning('Skipping test, because the client version is known to behave incorrectly')
        return

    step(2,'move the folder during the sync')

    syncdir = make_workdir("workdir")
    d1 = os.path.join(syncdir,"dir1")
    d2 = os.path.join(syncdir,"dir2")
    d3 = os.path.join(syncdir,"dir3")
    d4 = os.path.join(syncdir,"dir4")
    d5 = os.path.join(syncdir,"dir5")
    d6 = os.path.join(syncdir,"dir6")
    d_final = os.path.join(syncdir,"dirFinal")

    #Do it several time with one second interval to be sure we do it at lease once
    # during the propagation phase
    sleep(1)
    mkdir(d3)
    mv(d2+"/*",d3)

    sleep(1)
    mkdir(d4)
    mv(d3+"/*",d4)

    sleep(1)
    mkdir(d5)
    mv(d4+"/*",d5)

    sleep(1)
    mkdir(d6)
    mv(d5+"/*",d6)

    sleep(1)
    mkdir(d_final)
    mv(d6+"/*",d_final)

