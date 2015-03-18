from smashbox.script import config

import smashbox.utilities 

def reset_server_log_file():
    """ Deletes the existing server log file so that there is a clean
        log file for the test run
    """

    cmd = '%s rm -rf %s/owncloud.log' % (config.oc_server_shell_cmd, config.oc_server_datadirectory)
#    logger.info ('Removing existing server log file with command %s' % cmd)
    runcmd(cmd)


#def scrape_log_file(d):
def scrape_log_file():
    """ Copies over the server log file and searches it for specific strings

    :param d: The directory where the server log file is to be copied to

    """
    d = make_workdir()
    cmd = 'scp root@%s:%s/owncloud.log %s/.' % (config.oc_server, config.oc_server_datadirectory, d)
    rtn_code = runcmd(cmd)

#    logger.info('copy command returned %s', rtn_code)

    # search logfile for string (1 == not found; 0 == found):

    cmd = "grep -i \"integrity constraint violation\" %s/owncloud.log" % d
    rtn_code = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Integrity Constraint Violation\" message found in server log file")

    cmd = "grep -i \"Exception\" %s/owncloud.log" % d
    rtn_code = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Exception\" message found in server log file")

    cmd = "grep -i \"could not obtain lock\" %s/owncloud.log" % d
    rtn_code = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Could Not Obtain Lock\" message found in server log file")

    cmd = "grep -i \"db error\" %s/owncloud.log" % d
    rtn_code = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"DB Error\" message found in server log file")

    cmd = "grep -i \"stat failed\" %s/owncloud.log" % d
    rtn_code = runcmd(cmd, ignore_exitcode=True, log_warning=False)
    error_check(rtn_code > 0, "\"Stat Failed\" message found in server log file")

