
__doc__ = """ Test user and group management """

from smashbox.utilities import *
import glob

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account()

    step (2, 'check users created')
    check_users()

    step (3, 'create test groups')
    reset_owncloud_group()

    step (4, 'check groups created')
    check_groups

def check_users(numTestUsers=None):

   if numTestUsers is None:
     numTestUsers = config.oc_number_test_users

   for i in range(1, numTestUsers+1):
       username = "%s%i"%(config.oc_account_name, i)
       result = check_owncloud_account(username)
       error_check(int(result or 0) == 0, 'User %s not found'%username)

def check_groups(numGroups=1):

   for i in range(1, numGroups+1):
       groupname = "%s%i"%(config.oc_group_name, i)
       result = check_owncloud_group(groupname)
       error_check(int(result or 0) == 0, 'Group %s not found'%groupname)

