<?php

# Create local user account.
#
# Author: Jakub T. Moscicki, 2013, CERN/IT
#
# License: AGPL
#
# To be placed and run on the owncloud application server: 
#
#  php -f check_group.php GID 
#
# Example: check if group exists 
#
#   sudo -u apache php -f check_group.php  testGroup
#

set_include_path(get_include_path() . PATH_SEPARATOR . '/var/www/html/owncloud');

require_once 'lib/base.php';

$gid = $argv[1];

if(OC_Group::groupExists($gid)) {
  print "Group exists: ".$gid."\n";
  exit(0);
}
else
  {
    print "Group NOT FOUND:".$gid."\n";
    exit(1);    
  }

?>
