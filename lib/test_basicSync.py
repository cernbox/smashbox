__doc__ = """ Test basic sync and conflbfnicts: files are modified and deleted by one or both workers (winner and loser); optionally remove local state db on one of the clients (loser).

There are four clients (workers):

 - creator - populates the directory initially and also performs a final check
 - winner  - is syncing its local changes first
 - loser   - is syncing its local changes second (and optionally it looses the local sync database before doing the sync)
 - checker - only performs a final check (without having interacted with the system before)

Note: in 1.6 client conflict files are excluded by default - so they should be never propagated to the server
Note: in 1.5 the exclusion list should be provided separately to the client (FIXME)

Note on effects of removing local state db (1.6):

 - any files modified remotely or locally get a conflict if both remote and local replicas exist (FIXME: this could be possibly more refined in the future based on timestamps or content checksums)
 - any files not present locally but present remotely will be downloaded (so a deletion won't be propagated)

"""

from smashbox.utilities import * 

import glob

filesizeKB = int(config.get('basicSync_filesizeKB',10000))

# True => remove local sync db on the loser 
# False => keep the loser 
rmLocalStateDB = bool(config.get('basicSync_rmLocalStateDB',False))

# subdirectory where to put files (if empty then use top level workdir)
subdirPath = config.get('basicSync_subdirPath',"")

#### testsets = [
####         { 'basicSync_filesizeKB': 1, 
####           'basicSync_rmLocalStateDB':False
####         },
####         { 'basicSync_filesizeKB': 5000, 
####           'basicSync_rmLocalStateDB':False
####         },
####         { 'basicSync_filesizeKB': 15000, 
####           'basicSync_rmLocalStateDB':False
####         },
####         { 'basicSync_filesizeKB': 50000, 
####           'basicSync_rmLocalStateDB':False
####         },
#### 
####         { 'basicSync_filesizeKB': 1, 
####           'basicSync_rmLocalStateDB':True
####         },
####         { 'basicSync_filesizeKB': 5000, 
####           'basicSync_rmLocalStateDB':True
####         },
####         { 'basicSync_filesizeKB': 15000, 
####           'basicSync_rmLocalStateDB':True
####         },
####         { 'basicSync_filesizeKB': 50000, 
####           'basicSync_rmLocalStateDB':True
####         }
#### ]
#### 

testsets = []

# create cartesian product of all test configurations
for s in [1, 5000, 15000, 50000]:
  for t in [True, False]:
      for p in [ "", "abc", "abc/abc", "abc/def/ghi" ]:
          testsets.append( { 'basicSync_filesizeKB':s,
                             'basicSync_rmLocalStateDB':t,
                             'basicSync_subdirPath':p } )

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
def creator(step):
    
    reset_owncloud_account()
    reset_rundir()

    step(1,'create initial content and sync')

    d = make_workdir()

    # we put the files in the subdir
    subdir = os.path.join(d,subdirPath)

    mkdir(subdir) 


    # files *_NONE are not modified by anyone after initial sync
    # files *_LOSER are modified by the loser but not by the winner
    # files *_WINNER are modified by the winner but not by the loser
    # files *_BOTH are modified both by the winner and by the loser (always conflict on the loser)

    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_NONE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_LOSER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_WINNER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_BOTH.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_DELETED_LOSER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_DELETED_WINNER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_DELETED_BOTH.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_creator'] = md5sum(os.path.join(subdir,'TEST_FILE_MODIFIED_NONE.dat'))
    logger.info('md5_creator: %s',shared['md5_creator'])

    list_files(subdir)
    run_ocsync(d)
    list_files(subdir)

    step(7,'download the repository')
    run_ocsync(d,n=3)

    step(8,'final check')

    final_check(subdir,shared)
    expect_no_conflict_files(subdir) 

@add_worker
def winner(step):
    step(2,'initial sync')

    d = make_workdir()
    subdir = os.path.join(d,subdirPath)

    run_ocsync(d)

    step(3,'modify locally and sync to server')

    list_files(subdir)

    remove_file(os.path.join(subdir,'TEST_FILE_DELETED_WINNER.dat'))
    remove_file(os.path.join(subdir,'TEST_FILE_DELETED_BOTH.dat'))

    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_WINNER.dat'),'1',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_BOTH.dat'),'1',count=1000,bs=filesizeKB)

    createfile(os.path.join(subdir,'TEST_FILE_ADDED_WINNER.dat'),'1',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_ADDED_BOTH.dat'),'1',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_winner'] = md5sum(os.path.join(subdir,'TEST_FILE_ADDED_WINNER.dat'))
    logger.info('md5_winner: %s',shared['md5_winner'])

    run_ocsync(d)

    sleep(1.1) # csync: mtime diff < 1s => conflict not detected, see: #5589 https://github.com/owncloud/client/issues/5589

    step(5,'final sync')

    run_ocsync(d,n=3)

    step(8,'final check')

    final_check(subdir,shared)
    expect_no_conflict_files(subdir) 


# this is the loser which lost it's local state db after initial sync

@add_worker
def loser(step):

    step(2,'initial sync')

    d = make_workdir()
    subdir = os.path.join(d,subdirPath)

    run_ocsync(d)

    step(4,'modify locally and sync to the server')

    list_files(subdir)

    # now do the local changes

    remove_file(os.path.join(subdir,'TEST_FILE_DELETED_LOSER.dat'))
    remove_file(os.path.join(subdir,'TEST_FILE_DELETED_BOTH.dat'))

    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_LOSER.dat'),'2',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_MODIFIED_BOTH.dat'),'2',count=1000,bs=filesizeKB)

    createfile(os.path.join(subdir,'TEST_FILE_ADDED_LOSER.dat'),'2',count=1000,bs=filesizeKB)
    createfile(os.path.join(subdir,'TEST_FILE_ADDED_BOTH.dat'),'2',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_loser'] = md5sum(os.path.join(subdir,'TEST_FILE_ADDED_LOSER.dat'))
    logger.info('md5_loser: %s',shared['md5_loser'])


    #os.system('curl -v -s -k -XPROPFIND --data @/b/eos/CURL-TEST/p2.dat %s| xmllint --format -'%oc_webdav_url(remote_folder='TEST_FILE_MODIFIED_BOTH.dat'))
    #os.system('sqlite3 -line /tmp/smashdir/test_basicSync/loser/.csync_journal.db  \'select * from metadata where path like "%TEST_FILE_MODIFIED_BOTH%"\'')

    # remove the sync db
    if rmLocalStateDB:
       statedb_files=[]
       # pre-2.3 clients used a fixed name
       # 2.3 onwards use variable names: https://github.com/owncloud/client/blob/master/src/common/syncjournaldb.cpp#L69
       for p in ['.csync_journal.db','._sync_*.db','.sync_*.db']:
          statedb_files += glob.glob(os.path.join(d,p))

       fatal_check(len(statedb_files)==1,"expected journal file, not found")

       remove_file(statedb_files[0])

    run_ocsync(d,n=3) # conflict file will be synced to the server but it requires more than one sync run

    step(6,'final sync')
    run_ocsync(d)

    step(8,'final check')

    #os.system('sqlite3 -line /tmp/smashdir/test_basicSync/loser/.csync_journal.db  \'select * from metadata where path like "%TEST_FILE_MODIFIED_BOTH%"\'')

    final_check(subdir,shared)
    if not rmLocalStateDB:
        expect_conflict_files(subdir, ['TEST_FILE_ADDED_BOTH.dat', 'TEST_FILE_MODIFIED_BOTH.dat' ])
    else:
        expect_conflict_files(subdir, ['TEST_FILE_ADDED_BOTH.dat', 'TEST_FILE_MODIFIED_BOTH.dat', 
                                  'TEST_FILE_MODIFIED_LOSER.dat', 'TEST_FILE_MODIFIED_WINNER.dat']) # because the local and remote state is different and it is assumed that this is a conflict (FIXME: in the future timestamp-based last-restort check could improve this situation)

@add_worker
def checker(step):
    shared = reflection.getSharedObject()

    step(7,'download the repository for final verification')
    d = make_workdir()
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
    expect_content(os.path.join(d,'TEST_FILE_MODIFIED_NONE.dat'), shared['md5_creator'])

    expect_content(os.path.join(d,'TEST_FILE_ADDED_LOSER.dat'), shared['md5_loser'])

    if not rmLocalStateDB:
        expect_content(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'), shared['md5_loser'])
    else:
        expect_content(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'), shared['md5_creator']) # in this case, a conflict is created on the loser and file on the server stays the same

    expect_content(os.path.join(d,'TEST_FILE_ADDED_WINNER.dat'), shared['md5_winner'])
    expect_content(os.path.join(d,'TEST_FILE_MODIFIED_WINNER.dat'), shared['md5_winner']) 
    expect_content(os.path.join(d,'TEST_FILE_ADDED_BOTH.dat'), shared['md5_winner'])     # a conflict on the loser, server not changed
    expect_content(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'), shared['md5_winner'])  # a conflict on the loser, server not changed

    if not rmLocalStateDB:
        expect_no_deleted_files(d) # normally any deleted files should not come back
    else:
        expect_deleted_files(d, ['TEST_FILE_DELETED_LOSER.dat', 'TEST_FILE_DELETED_WINNER.dat']) # but not TEST_FILE_DELETED_BOTH.dat !
        expect_content(os.path.join(d,'TEST_FILE_DELETED_LOSER.dat'), shared['md5_creator']) # this file should be downloaded by the loser because it has no other choice (no previous state to compare with)
        expect_content(os.path.join(d,'TEST_FILE_DELETED_WINNER.dat'), shared['md5_creator']) # this file should be re-uploaded by the loser because it has no other choice (no previous state to compare with)

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
