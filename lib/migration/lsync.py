# IMG_20171005_105458.jpg : REMOVED
# IMG_20171005_105509.jpg : RENAMED -> IMG_20171005_105509-RENAMED.jpg
# IMG_20171005_105517.jpg : NOT CHANGED
# IMG_20171005_110734.jpg : NOT CHANGED
# NEW.txt		  : NEW FILE


from smashbox.utilities import *

import glob

subdirPath = ""
filesizeKB = 5000

def expect_content(fn,md5):
    actual_md5 = md5sum(fn)
    error_check(actual_md5 == md5, "inconsistent md5 of %s: expected %s, got %s"%(fn,md5,actual_md5))

def expect_no_deleted_files(d):
    expect_deleted_files(d,[])

def expect_deleted_files(d,expected_deleted_files):
    actual_deleted_files = glob.glob(os.path.join(d,'*_DELETED*'))
    logger.debug('deleted files in %s: %s',d,actual_deleted_files)

    error_check(len(expected_deleted_files) == len(actual_deleted_files), "expected %d got %d deleted files"%(len(expected_deleted_files),len(actual_deleted_files)))

    for fn in expected_deleted_files:
        error_check(any([fn in dfn for dfn in actual_deleted_files]), "expected deleted file for %s not found"%fn)


def expect_conflict_files(d,expected_conflict_files):
    actual_conflict_files = glob.glob(os.path.join(d,'*_conflict-*-*'))

    logger.debug('conflict files in %s: %s',d,actual_conflict_files)

    error_check(len(expected_conflict_files) == len(actual_conflict_files), "expected %d got %d conflict files"%(len(expected_conflict_files),len(actual_conflict_files)))

    exp_basefns = [os.path.splitext(fn)[0] for fn in expected_conflict_files]

    logger.debug(exp_basefns)
    logger.debug(actual_conflict_files)

    for bfn in exp_basefns:
        error_check(any([bfn in fn for fn in actual_conflict_files]), "expected conflict file for %s not found"%bfn)

def expect_no_conflict_files(d):
    expect_conflict_files(d,[])


@add_worker
def winner(step):
    import shutil

    step(2,'initial sync')

    #d = make_workdir()
    d = '/root/ownCloud/'
    subdir = os.path.join(d,subdirPath)

    print "WORKDIR:" + d

    run_ocsync(d)

    sleep(1.1) # csync: mtime diff < 1s => conflict not detected

    step(3,'modify locally and sync to server')

    list_files(subdir)

    remove_file(os.path.join(subdir,'IMG_20171005_105458.jpg'))

    createfile(os.path.join(subdir,'NEW.txt'),'1',count=1000,bs=filesizeKB)

    shutil.move(os.path.join(subdir, 'IMG_20171005_105509.jpg'), os.path.join(subdir, 'IMG_20171005_105509-RENAMED.jpg'))

    createfile(os.path.join(subdir,'test.txt'),'1',count=1000,bs=filesizeKB)



    shared = reflection.getSharedObject()

    shared['md5_NEW'] = md5sum(os.path.join(subdir,'NEW.txt'))
    logger.info('md5_NEW: %s',shared['md5_NEW'])

    shared['md5_IMG_20171005_105509-RENAMED.jpg'] = md5sum(os.path.join(subdir,'IMG_20171005_105509-RENAMED.jpg'))
    logger.info('md5_IMG_20171005_105509-RENAMED.jpg: %s',shared['md5_IMG_20171005_105509-RENAMED.jpg'])

    shared['md5_test'] = md5sum(os.path.join(subdir,'test.txt'))
    logger.info('md5_test: %s',shared['md5_test'])



    run_ocsync(d)

    sleep(1.1) # csync: mtime diff < 1s => conflict not detected, see: #5589 https://github.com/owncloud/client/issues/5589

    step(5,'final sync')

    run_ocsync(d,n=3)

    step(8,'final check')

    final_check(subdir,shared)
    expect_no_conflict_files(subdir)



@add_worker
def checker(step):
    shared = reflection.getSharedObject()

    step(7,'download the repository for final verification')
    #d = make_workdir()
    d = '/root/ownCloud/'
    subdir = os.path.join(d,subdirPath)

    run_ocsync(d,n=3)

    step(8,'final check')

    final_check(subdir,shared)
    expect_no_conflict_files(subdir)


def final_check(d,shared):
    """ This is the final check applicable to all workers - this reflects the status of the remote repository so everyone should be in sync.
    The only potential differences are with locally generated conflict files.
    """

    list_files(d)
    expect_content(os.path.join(d,'NEW.txt'), shared['md5_NEW'])
    expect_content(os.path.join(d,'IMG_20171005_105509-RENAMED.jpg'), shared['md5_IMG_20171005_105509-RENAMED.jpg'])
    expect_content(os.path.join(d,'test.txt'), shared['md5_test'])
    #expect_deleted_files(d, ['IMG_20171005_105458.jpg'])

###############################################################################

def final_check_1_5(d): # this logic applies for 1.5.x client and owncloud server...
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


