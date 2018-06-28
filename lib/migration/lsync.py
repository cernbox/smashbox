# IMG_20171005_105458.jpg : REMOVED
# IMG_20171005_105509.jpg : RENAMED -> IMG_20171005_105509-RENAMED.jpg
# IMG_20171005_105517.jpg : NOT CHANGED
# IMG_20171005_110734.jpg : NOT CHANGED
# NEW.txt		  : NEW FILE
# NEW_BIG.txt                 : NEW BIG FILE
# test.txt		  : MODIFY EXISTING FILE
# BigFile		  : MODIFY BIG EXISTING FILE
# torename.txt		  : RENAME FILE TO EXISTING FILE -> existing.txt

# Photos/IMG_20180615_224839.jpg : MOVED -> FOLDERX
# FOLDER_MOVED			 : MOVED -> FOLDERX


from smashbox.utilities import *

import glob

subdirPath = ""
filesizeKB = 5000

FOLDER_FILES = ['IMG_20180615_224839.jpg', 'IMG_20180615_224840.jpg', 'IMG_20180616_232842.jpg']


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

    remove_file(os.path.join(subdir,'IMG_20171005_105458.jpg')) 	# IMG_20171005_105458.jpg : REMOVED
    createfile(os.path.join(subdir,'NEW.txt'),'1',count=1000,bs=filesizeKB)	# NEW.txt : NEW FILE
    createfile(os.path.join(subdir,'NEW_BIG.txt'),'1',count=20000,bs=filesizeKB)     # NEW_BIG.txt : NEW BIG FILE
    shutil.move(os.path.join(subdir, 'IMG_20171005_105509.jpg'), os.path.join(subdir, 'IMG_20171005_105509-RENAMED.jpg')) 	# IMG_20171005_105509.jpg : RENAMED -> IMG_20171005_105509-RENAMED.jpg
    createfile(os.path.join(subdir,'test.txt'),'1',count=1000,bs=filesizeKB)	# test.txt : MODIFY EXISTING FILE
    shutil.move(os.path.join(subdir, 'torename.txt'), os.path.join(subdir, 'existing.txt'))
    shutil.move(os.path.join(subdir, 'Photos/IMG_20180615_224839.jpg'), os.path.join(subdir, 'FOLDERX/IMG_20180615_224839.jpg'))	# Photos/IMG_20180615_224839.jpg : MOVED -> FOLDERX
    mv(os.path.join(subdir, 'FOLDER_MOVED'), os.path.join(subdir, 'FOLDERX/FOLDER_MOVED'))	# FOLDER_MOVED : MOVED -> FOLDERX
    createfile(os.path.join(subdir,'BigFile'),'1',count=15000,bs=filesizeKB)	# BigFile: MODIFY BIG EXISTING FILE


    shared = reflection.getSharedObject()

    shared['md5_NEW'] = md5sum(os.path.join(subdir,'NEW.txt'))
    logger.info('md5_NEW: %s',shared['md5_NEW'])

    shared['md5_NEW_BIG'] = md5sum(os.path.join(subdir,'NEW_BIG.txt'))
    logger.info('md5_NEW_BIG: %s',shared['md5_NEW_BIG'])

    shared['md5_IMG_20171005_105509-RENAMED.jpg'] = md5sum(os.path.join(subdir,'IMG_20171005_105509-RENAMED.jpg'))
    logger.info('md5_IMG_20171005_105509-RENAMED.jpg: %s',shared['md5_IMG_20171005_105509-RENAMED.jpg'])

    shared['md5_test'] = md5sum(os.path.join(subdir,'test.txt'))
    logger.info('md5_test: %s',shared['md5_test'])

    shared['md5_IMG_20180615_224839.jpg'] = md5sum(os.path.join(subdir,'FOLDERX/IMG_20180615_224839.jpg'))
    logger.info('md5_IMG_20180615_224839.jpg: %s',shared['md5_IMG_20180615_224839.jpg'])

    shared['md5_existing'] = md5sum(os.path.join(subdir,'existing.txt'))
    logger.info('md5_existing: %s',shared['md5_existing'])

    shared['md5_BigFile'] = md5sum(os.path.join(subdir,'BigFile'))
    logger.info('md5_BigFile: %s',shared['md5_BigFile'])


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
    expect_content(os.path.join(d,'NEW_BIG.txt'), shared['md5_NEW_BIG'])
    expect_content(os.path.join(d,'IMG_20171005_105509-RENAMED.jpg'), shared['md5_IMG_20171005_105509-RENAMED.jpg'])
    expect_content(os.path.join(d,'test.txt'), shared['md5_test'])
    expect_content(os.path.join(d,'existing.txt'), shared['md5_existing'])
    expect_content(os.path.join(d,'FOLDERX/IMG_20180615_224839.jpg'), shared['md5_IMG_20180615_224839.jpg'])
    expect_content(os.path.join(d,'BigFile'), shared['md5_BigFile'])

    d1 = os.path.join(d,'FOLDER_MOVED')
    d2 = os.path.join(d, 'FOLDERX/FOLDER_MOVED')
    logger.info('checking %s',d1)
    error_check(not os.path.exists(d1), "path %s should not exist"%d1)

    logger.info('checking %s',d2)
    error_check(os.path.isdir(d2), "path %s should be a directory"%d2)

    for fn in FOLDER_FILES:
        f = os.path.join(d2,fn)
        logger.info("checking %s",f)
        error_check(os.path.isfile(f), "path %s should be a file"%f)


