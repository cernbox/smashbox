
__doc__ = "This example shows the testcases."

# import utilities which are the building block of each testcase
from smashbox.utilities import *

A = int(config.get('hello3_A',0))
B = int(config.get('hello3_B',0))

testsets = [{"hello3_A":1,"hello3_B":2},{"hello3_A":111,"hello3_B":222}]

logger.info("Loading tescase module...")

@add_worker
def helloA(step):
    step(1)

    logger.info("My A=%d",A)


@add_worker
def helloB(step):
    step(2)

    logger.info("My B=%d",B)



@add_worker
def helloC(step):
    step(3)

    logger.info("My A+B=%d",A+B)
