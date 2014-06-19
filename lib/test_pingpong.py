from smashbox.utilities import * 
from smashbox.utilities.hash_files import count_files

__doc__ = """ Test parallel upload of the same file by two clients.

The name of the test derives from the behaviour observed with eos webdav endpoint: two file versions would ping-pong between the clients.

"""

filesizeKB = int(config.get('pinpong_filesizeKB',5000))


@add_worker
def ping(step):
    
    reset_owncloud_account()
    reset_rundir()

    shared = reflection.getSharedObject()

    step(1,'initialize')

    d = make_workdir()

    createfile(os.path.join(d,'BALL'),'0',count=1000,bs=filesizeKB)

    BALL = md5sum(os.path.join(d,'BALL'))
    logger.info('BALL: %s',BALL)

    shared['PING_BALL'] = BALL

    step(2,'first sync')
    run_ocsync(d,N=1)
    LAST_BALL = md5sum(os.path.join(d,'BALL'))

    for i in range(3,10):
        step(i,'next sync')
        run_ocsync(d)
        BALL = md5sum(os.path.join(d,'BALL'))
        logger.info('BALL: %s',BALL)
        error_check( BALL == LAST_BALL, "the file is ping-ponging between the clients")
        LAST_BALL = BALL



@add_worker
def pong(step):

    step(1,'initialize')

    d = make_workdir()
    shared = reflection.getSharedObject()

    createfile(os.path.join(d,'BALL'),'1',count=1000,bs=filesizeKB)

    BALL = md5sum(os.path.join(d,'BALL'))
    logger.info('BALL: %s',BALL)

    shared['PONG_BALL'] = BALL

    step(2,'first sync')
    run_ocsync(d,N=1)
    LAST_BALL = md5sum(os.path.join(d,'BALL'))

    for i in range(3,10):
        step(i,'next sync')
        run_ocsync(d)
        BALL = md5sum(os.path.join(d,'BALL'))
        logger.info('BALL: %s',BALL)
        error_check( BALL == LAST_BALL, "the file is ping-ponging between the clients")
        LAST_BALL = BALL


