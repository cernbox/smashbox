from smashbox.utilities import * 

__doc__ = """ Test basic sync and conflicts: files are modified and deleted by one or both workers (winner and loser); optionally remove local state db on one of the clients (loser).

There are four clients (workers):

 - creator - populates the directory initially and also performs a final check
 - winner  - is syncing its local changes first
 - loser   - is syncing its local changes second (and optionally it looses the local sync database before doing the sync)
 - checker - only performs a final check (without having interacted with the system before)

FIXME: file exclusion list should be prvided correctly (from mirall or owncloudcmd) - otherwise test conflict files are demonstrated to be uploaded to the server 

"""

filesizeKB = int(config.get('basicSync_filesizeKB',10000))

# True => remove local sync db on the loser 
# False => keep the loser 
rmLocalStateDB = bool(config.get('basicSync_rmLocalStateDB',False))
    
@add_worker
def creator(step):
    
    reset_owncloud_account()
    reset_rundir()

    step(1,'create initial content and sync')

    d = make_workdir()

    # files *_NONE are not modified by anyone after initial sync
    # files *_LOSER are modified by the loser but not by the winner
    # files *_WINNER are modified by the winner but not by the loser
    # files *_BOTH are modified both by the winner and by the loser (always conflict on the loser)

    createfile(os.path.join(d,'TEST_FILE_MODIFIED_NONE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_WINNER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_DELETED_LOSER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_DELETED_WINNER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_DELETED_BOTH.dat'),'0',count=1000,bs=filesizeKB)
    
    run_ocsync(d)

    step(7,'download the repository')
    run_ocsync(d)

    final_check(d)

@add_worker
def winner(step):
    step(2,'initial sync')

    d = make_workdir()
    run_ocsync(d)

    step(3,'modify locally and sync to server')

    removeFile(os.path.join(d,'TEST_FILE_DELETED_WINNER.dat'))
    removeFile(os.path.join(d,'TEST_FILE_DELETED_BOTH.dat'))

    createfile(os.path.join(d,'TEST_FILE_MODIFIED_WINNER.dat'),'1',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'),'1',count=1000,bs=filesizeKB)

    run_ocsync(d)

    step(5,'final sync')

    run_ocsync(d,N=3)

    final_check(d)

# this is the loser which lost it's local state db after initial sync

@add_worker
def loser(step):

    step(2,'initial sync')

    d = make_workdir()
    run_ocsync(d)

    step(4,'modify locally and sync to the server')

    # now do the local changes

    removeFile(os.path.join(d,'TEST_FILE_DELETED_LOSER.dat'))
    removeFile(os.path.join(d,'TEST_FILE_DELETED_BOTH.dat'))

    createfile(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'),'2',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'),'2',count=1000,bs=filesizeKB)

    # remove the sync db
    if rmLocalStateDB:
        removeFile(os.path.join(d,'.csync_journal.db'))

    run_ocsync(d,N=3) # conflict file will be synced to the server but it requires more than one sync run

    step(6,'final sync')
    run_ocsync(d)

    final_check(d)

@add_worker
def checker(step):
    
    step(7,'download the repository for final verification')
    d = make_workdir()
    run_ocsync(d)
    
    final_check(d)


def final_check(d):
    """ Final verification: all local sync folders should look the same. We expect conflicts and handling of deleted files depending on the rmLocalStateDB option. See code for details.
    """
    import glob

    list_files(d)
    
    conflict_files = glob.glob(os.path.join(d,'*_conflict-*-*'))

    logger.debug('conflict files in %s: %s',d,conflict_files)

    if not rmLocalStateDB:
        # we expect exactly 1 conflict file

        logger.warning("FIXME: currently winner gets a conflict file - exclude list should be updated and this assert modified for the winner")

        error_check(len(conflict_files) == 1, "there should be exactly 1 conflict file (%d)"%len(conflict_files))
    else:
        # we expect exactly 3 conflict files
        error_check(len(conflict_files) == 3, "there should be exactly 3 conflict files (%d)"%len(conflict_files))

    for fn in conflict_files:

        if not rmLocalStateDB:
            error_check('_BOTH' in fn, """only files modified in BOTH workers have a conflict -  all other files should be conflict-free""")

        else:
            error_check('_BOTH' in fn or '_LOSER' in fn or '_WINNER' in fn, """files which are modified by ANY worker have a conflict now;  files which are not modified should not have a conflict""")

    deleted_files = glob.glob(os.path.join(d,'*_DELETED*'))

    logger.debug('deleted files in %s: %s',d,deleted_files)

    if not rmLocalStateDB:
        error_check(len(deleted_files) == 0, 'deleted files should not be there normally')
    else:
        # deleted files "reappear" if local sync db is lost on the loser, the only file that does not reappear is the DELETED_BOTH which was deleted on *all* local clients

        error_check(len(deleted_files) == 2, "we expect exactly 2 deleted files")

        for fn in deleted_files:
            error_check('_LOSER' in fn or '_WINNER' in fn, "deleted files should only reappear if delete on only one client (but not on both at the same time) ")
