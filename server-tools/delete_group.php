<?php

# Create local user account.
#
# Author: Jakub T. Moscicki, 2013, CERN/IT
#
# License: AGPL
#
# To be placed and run on the owncloud application server: 
#
#  php -f delete_user.php USER
#
# Example: delete test groups 
#
#   sudo -u apache php -f /b/poc/tools/delete_group.php testGroup
#

set_include_path(get_include_path() . PATH_SEPARATOR . '/var/www/html/owncloud');

require_once 'lib/base.php';

$gid = $argv[1];

print "deleting group ... \n";
OC_Group::deleteGroup($gid);

?>
