
# this is all-in-one example which shows various aspects of the smashbox framework

# import utilities which are the building block of each testcase
from smashbox.utilities import *
from smashbox.utilities import reflection

# all normal output should go via logger.info()
# all additional output should go via logger.debug()

logger.info("THIS IS A HELLO WORLD EXAMPLE")

logger.debug("globals() %s",globals().keys())


# Workers run as independent processes and wait for each other at each
# defined step: a worker will not enter step(N) until all others have
# completed step(N-1). A worker waiting at step(N) has already
# implicitly completed all steps 0..N-1

@add_worker
def helloA(step):
    logger.debug("globals() %s",globals().keys())


    # Sharing of variables between workers - see below.
    shared = reflection.getSharedObject()

    step(0,'defining n')
    
    shared['n'] = 111
    
    # Variable 'n' is now shared and visible to all the workers.
    # This happens when a value of the variable is assigned.
    #
    # Limitations: Workers A and B should not modify the same shared
    # variable in parallel (that it in the same step). Also that
    # worker that sets the variable should do it in a step preceding
    # the steps in which other workers are making use of it. Only this
    # will guarantee that the value is set before someone else is
    # trying to make use of it.
    # 
    # If you need more than one worker to modify the same
    # shared variable make sure this happens in separate steps.


    step(1,'defining xyz')

    # Contrary to the plain types (string,int,float) here we share a list - see limitations below.
    shared['xyz'] = [1,2,3]

    # If you modify the value in place of a shared.attribute
    # (e.g. list.append or list.sort) then this is NOT visible to other
    # processes until you really make the assignment.
    # 
    # Some ideas how to handle lists by assigning a new value:
    #   * use shared['list']+=[a] instead of shared['list'].append(a)
    #   * use shared['list']=sorted(shared['list']) instead of shared['list'].sort() 
    #
    step(2,'waiting...')

    step(3,'checking integrity')

    # this is an non-fatal assert - error will be rerpoted and test marked as failed but execution will continue
    error_check(shared['n']==222, 'problem handling shared n=%d'%shared['n'])

    # this is a fatal assert - execution will stop immediately
    fatal_check(list(shared['xyz'])==[1,2,3,4], 'problem handlign shared xyz=%s'%repr(shared['xyz']))
    
@add_worker 
def helloB(step):
    logger.debug("dir() %s",dir())
    
    shared = reflection.getSharedObject()

    step(2,'modifying and reassigning n, xyz')
    shared['n'] += 111
    shared['xyz'] += [4]

    step(3, 'checking integrity')
    error_check(shared['n']==222, 'problem handling shared n=%d'%shared['n'])
    error_check(list(shared['xyz'])==[1,2,3,4], 'problem handlign shared xyz=%s'%repr(shared['xyz']))


@add_worker    
def reporter(step):
    shared = reflection.getSharedObject()

    # report on shared objects at every step
    for i in range(5): # until the last step used in this example
        step(i)
        logger.info("shared: %s",str(shared))

# this shows how workers with the same function body may be added in a loop any number of times

# shared.k is an example on how NOT to use the shared object -- see comments at the top of this file
# this worker code will run N times in parallel -- see below
def any_worker(step):
    shared=reflection.getSharedObject()

    shared['k'] = 0
    
    step(1,None)

    shared['k'] += 1

    step(2,None)
    shared['k'] += 1
    
    step(3,None)
    shared['k'] += 1

    step(4,'finish')

    logger.info("k=%d, expected %d",shared['k'],N*3)
    # one would assume here that shared.k == N*3, however as the
    # assignments to shared.k are not atomic and may happen in parallel this is not reliable.
    # just don't do this kind of thing!

# this shows how one may add configuration parameters to the testcase
N = int(config.get('n_hello_workers',5))
    
logger.info("will create %d additional workers",N)

# here we add the workers (and append the number to each name)
for i in range(N):
    add_worker(any_worker,'any_worker%d'%i)
    
    
