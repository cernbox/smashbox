<?php

# Create local user account.
#
# Author: Jakub T. Moscicki, 2013, CERN/IT
#
# License: AGPL
#
# To be placed and run on the owncloud application server: 
#
#  php -f create_group.php gid
#
# Example: create test group
#
#   sudo -u apache php -f create_group.php testGroup
#

set_include_path(get_include_path() . PATH_SEPARATOR . '/var/www/html/owncloud');

require_once 'lib/base.php';

$gid = $argv[1];

if(OC_Group::groupExists($gid)) {
  print "group already exists:".$gid."\n";
}
else
  {
    print "creating group... \n";
    OC_Group::createGroup($gid);
    print "group created:".$gid."\n";
  }

?>
