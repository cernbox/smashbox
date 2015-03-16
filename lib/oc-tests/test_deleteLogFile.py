
__doc__ = """

Test a remote delete of the server log file 

"""

from smashbox.utilities import *
import glob

@add_worker
def scrapeServerLog(step):

    step (1, 'create directory for server log')
    reset_server_log_file()

