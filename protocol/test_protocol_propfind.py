from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import *

@add_worker
def main(step):

    d = make_workdir()
    reset_owncloud_account()

    URL = oc_webdav_url()

    ls_prop_desktop20(URL,depth=0)
    logger.info("Passed 1")

    ls_prop_desktop20(URL,depth=1)
    logger.info("Passed 2")

    ls_prop_desktop17(URL,depth=0)
    logger.info("Passed 3")

    ls_prop_desktop17(URL,depth=1)
    logger.info("Passed 4")

    all_prop_android(URL,depth=0)
    logger.info("Passed 5")

    all_prop_android(URL,depth=1)
    logger.info("Passed 6")
