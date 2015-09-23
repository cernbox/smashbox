
__doc__ = """ Concurrently upload the same large file by two sync clients. It may ne necessary to run mulitple times. In owncloud 5.0.10 this testcase triggers a race condition which is reported in the following way:

2013-11-13 15:54:23,039 - INFO - checker - shared w0d1 af27141daa272ef2285695fe8e709d9f
2013-11-13 15:54:23,039 - INFO - checker - shared w0v1 19987ddec02a36d6403a274565032045
2013-11-13 15:54:23,040 - INFO - checker - shared w0v2 af27141daa272ef2285695fe8e709d9f
2013-11-13 15:54:23,040 - INFO - checker - shared w1d1 19987ddec02a36d6403a274565032045
2013-11-13 15:54:23,040 - INFO - checker - shared w1d2 ffffc84eaed851baa0e61b554aa90daa
2013-11-13 15:54:23,041 - INFO - checker - shared w1v1 ffffc84eaed851baa0e61b554aa90daa
2013-11-13 15:54:23,041 - INFO - checker - shared w2d1 ffffc84eaed851baa0e61b554aa90daa

2013-11-13 15:54:24,337 - ERROR - checker - a version af27141daa272ef2285695fe8e709d9f (filename test.BIG.v1384354395) does not correspond to any previously generated file


"""
import time
import tempfile
import glob

from smashbox.utilities import * 
from smashbox.utilities import reflection

@add_worker
def worker0(step):
    shared = reflection.getSharedObject()
    
    reset_owncloud_account()
    reset_rundir()

    #versions = get_md5_versions_on_server('test.BIG')    
    
    step(1,'create initial content and sync')

    d = make_workdir()
    fn = '%s/test.BIG'%d
    createfile(fn,'0',count=100000,bs=1000)
    shared['w0v1'] = md5sum(fn)
    logger.info(shared['w0v1'])
    hexdump(fn)

    run_ocsync(d)

    step(3,'modify local content')

    createfile(fn,'1',count=200,bs=1000000) # create large file -> it will take longer to sync
    shared['w0v2'] = md5sum(fn)
    logger.info(shared['w0v2'])
    hexdump(fn)

    step(4,'sync local content')

    run_ocsync(d)

    shared['w0d1'] = md5sum(fn)
    logger.info(shared['w0d1'])
    hexdump(fn)

    if shared['w0d1'] == shared['w0v2']:
        logger.info("Content NOT changed locally")
    else:
        logger.info("CONTENT CHANGED LOCALLY")
    
    #step(4)
    #run_ocsync(d)
    #step(5)
    logger.info('output %s',d)


@add_worker
def worker1(step):
    shared = reflection.getSharedObject()
    
    step(2,'sync initial state created by worker 0')

    d = make_workdir()
    run_ocsync(d)

    fn = '%s/test.BIG'%d

    shared['w1d1'] = md5sum(fn)
    logger.info(shared['w1d1'])
    error_check(shared['w1d1'] == shared['w0v1'],'downloaded files does not match the initially created file')

    step(3,'modify local content')

    createfile(fn,'2',count=200000,bs=1000) # create large file -> it will take longer to sync

    shared['w1v1'] = md5sum(fn)
    logger.info(shared['w1v1'])
    hexdump(fn)

    step(4,'sync modified file')

    # add a bit of delay to make sure worker1 starts later than worker0
    sleep(2)

    run_ocsync(d)

    shared['w1d2'] = md5sum(fn)
    logger.info(shared['w1d2'])
    hexdump(fn)

    step(5)

    logger.info('output %s',d)


@add_worker
def checker(step):
    shared = reflection.getSharedObject()
    
    step(6,'sync the final state of the repository into a fresh local folder')
    #sleep(10)

    d = make_workdir()
    run_ocsync(d)

    fn = '%s/test.BIG'%d
    
    shared['w2d1'] = md5sum(fn)
    logger.info(shared['w2d1'])

    # print the status
    logger.info('final output %s',d)
    logger.info('content as reported by webdav')

    #DISABLED FOR NOW
    #list_versions_on_server('test.BIG')

    for x in sorted(shared.keys()):
        logger.info('shared %s %s',x,shared[x])

    # verify the status

    error_check(shared['w2d1'] in [shared['w0v1'],shared['w0v2'],shared['w1v1']], "file downloaded by the checker does not correspond to any file created locally by the workers")

    if False:
       # DISABLED FOR NOW 
       # make sure that all versions stored on a server correpond to a version generated locally
       versions = get_md5_versions_on_server('test.BIG')
       
       for v5,name in versions:
           error_check(not v5 in [shared['w0v1'],shared['w0v2'], shared['w1v1']],
                       'a version %s (filename %s) does not correspond to any previously generated file'%(v5,name))
   

    ### ASSERT
    # make sure it is empty
    #assert(glob.glob(d+'/*') == [])

