
__doc__ = """

Test copying over the server log file and searching it for some better known nasty errors

"""

from smashbox.utilities import *
import glob

@add_worker
def scrapeServerLog(step):

    step (1, 'create directory for server log')
    d = make_workdir()

    step (2, 'scrape log file for errors')
    scrape_log_file(d)

