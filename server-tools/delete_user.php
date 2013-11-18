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
# Example: delete test accounts
#
#   for i in {1..100}; do sudo -u apache php -f /b/poc/tools/delete_user.php test`printf "%03d\n" $i`; done
#

set_include_path(get_include_path() . PATH_SEPARATOR . '/var/www/html/owncloud');

require_once 'lib/base.php';

$login = $argv[1];

print "deleting user... \n";
OC_User::deleteUser($login);

?>
