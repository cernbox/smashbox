
# this example shows the logic of handling fatal errors

# import utilities which are the building block of each testcase
from smashbox.utilities import *
from smashbox.utilities import reflection

@add_worker
def helloA(step):
    step(1)

    fatal_check(False,'this is a FATAL error')


@add_worker
def helloB(step):
    step(1)

    fatal_check(False,'this is a FATAL error')


@add_worker
def helloC(step):
    step(2)

    logger.error('Executing post fatal handler')
