<?php

# Create local user account.
#
# Author: Jakub T. Moscicki, 2013, CERN/IT
#
# License: AGPL
#
# To be placed and run on the owncloud application server: 
#
#  php -f create_user.php USER PASSWORD
#
# Example: create test accounts
#
#   for i in {1..100}; do sudo -u apache php -f create_user.php test`printf "%03d\n" $i` "password" ; done
#

set_include_path(get_include_path() . PATH_SEPARATOR . '/var/www/html/owncloud');

require_once 'lib/base.php';

$login = $argv[1];

if(OC_User::userExists($login)) {
  print "user account exists:".$login."\n";
  exit(0);
}
else
  {
    print "user account NOT FOUND:".$login."\n";
    exit(1);    
  }

?>
