Overview
========

This is a framework for end-to-end testing the core storage functionality of 
owncloud-based service installation. This test framework may be run interactively from a command line, perform continous testing via cron jobs or stress/load testing. It may be easily integrated in testing and QA process.

What we check:
   * sync clients in various scenarios
   * trashbin and versioning
   * sharing of files and folders
   * basic protocol checks and documentation

The goal of this is to:
   * make sure that behaviour of the system is understood and not 
     changing unintentionally
   * reproduce difficult bugs more easily
   * a testcase is better way of reporting and documenting bugs 
     or undesider behaviour to the developers
   * provide a broad test coverage given a large number of setups and platforms

If you think you see a bug - write a test-case and let others
reproduce it on their systems.

This modification provides the possibility of:
   * running multiple test scenarios, aggregate them in groups by runid and store remotely in the database. Currently supported database is INFLUXDB, if 	 you want to get access to the already working database,graph displaying and aggregating webserver, please contact me at piotr.mrowczynski@yahoo.com.
   * you can test your service and compare specific scenarios with dropbox and seafile clients. 


This is work in progress. 

Project tree
============

General layout:

<pre>

   smashbox
   ├── bin/
   │   └── smash*                               : main test driver + other utilities for direct shell use
   ├── etc/				
   │   └── smashbox.conf                        : configuration file - this is also the default configuration for smashbox/bin utilities and for test-cases
   ├── lib/                                     : main collection of test-cases
   │   └── performance/                   		: here is the collection of performance test-cases
   │   		└── test_syncperf.py  			        
   │   ├── test_nplusone.py			
   │   └── ...  			        
   ├── protocol/                                : sync protocol tests and documentation
   ├── python/                                  : implementation of tools and API library for tests
   │   └── smashbox/utilities                   : here is the utilities used directly in the test-cases
   │   └── smashbox/test_manager                : that is the directory containing all the reporting features, also dropbox and seafile engines plugins
   ├── server/                                  : server-side procedures used in the tests
   ├── client/                                  : owncloud client helpers 
   │   └── compile-owncloud-sync-client*        : 
   ├── smashbox-deamon                          : This is the core executable file to handle reporting and aggregating of the files 
   └── README                                   : this file
   
</pre>

Installation of prerequisites
============

Note: Currently this framework works on Unix-like systems only. Windows port is needed.

Login as root, if you are willing to use sniffer, if not, you can stay as normal user. 

``sudo su``

and cd to ``/root/`` on your new Virtual Machine

`` cd ``

Install git

``apt-get update``

``apt-get install git-all``

``apt-get install curl``

``apt-get install python-pycurl``

``apt-get install python-netifaces``

Clone git repository into your local ``smashbox`` directory.

``git clone https://github.com/mrow4a/smashbox.git``

Comment:
if, for some reason you would like to use specific deic-client, you should 

``git clone https://github.com/mrow4a/deicclient.git``

Install owncloud client, as described at

``https://software.opensuse.org/download/package?project=isv:ownCloud:desktop&package=owncloud-client``

Dropbox Installation
============

If you are willing to use ``dropbox``, you should go to ``smashbox`` directory,

run ``bin/smash -o oc_account_password=dropbox -o engine=dropbox --testset 0 lib/performance/test_syncperf.py``

If you are on the text-based system, information about accessing the link and enabling dropbox client will appear. If it is desktop system, it will open the dropbox desktop client so that you could enter credentials for the dropbox account.

IMPORTANT! While you initialize dropbox using some user, you have to use the same user during execution of the tests. If you used root to initialize dropbox, you need to run test as a root. Otherwise, initialization will start again.

Seafile Installation
============

For Seafile client, first you need to set up the certificates on ubuntu, because the latest CLI client uses http protocol for synchronization. If you use https on the Seafile server side, you can't connect to the server from a Debian/Ubuntu machine using this CLI client:

<pre>
sudo mkdir -p /etc/pki/tls/certs
sudo cp /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt
sudo ln -s /etc/pki/tls/certs/ca-bundle.crt /etc/pki/tls/cert.pem
</pre>

If you will skip this step, your seafile will freeze on ``Starting to download ...``

First test runs
===============

On you owncloud account, create folder named ``testfolder`` or any name you are specifying as ``oc_server_folder`` in configuration file YOUR_NAME_FOR_FILE.config

Config JSON has a structure:

<pre>

   YOUR_NAME_FOR_FILE.config
   │
   ├── config
   │   ├── remote                                 : true/false | specifies if you would like to use remote storage
   │   ├── sniffer                                : true/false | specifies if you would like to catch all the packets flowing
   │   ├── backuplog                              : true/false | specifies if you would like to backup your test results to ``smashdir`` directory
   │   ├── remote_storage_server                  : ip address of your storage server - currently InfluxDB only supported
   │   ├── remote_database                        : name of the database at storage server 
   │   ├── remote_storage_user                    : database user 
   │   └── remote_storage_password                : database password 
   │
   ├── sync_engines
   │   ├── engine                                 : owncloud/dropbox/seafile | currently only those are supported
   │   ├── oc_server                              : server address | for seafile, use begining https://  e.g. https://seacloud.cc/
   │   ├── oc_account_name                        : dropbox/owncloud account name/seafile account name 
   │   ├── oc_account_password                    : dropbox/owncloud account password/seafile account password
   │   ├── oc_server_folder                       : dropbox/owncloud account folder e.g. testfolder /seafile account lib which is XXX at https://seacloud.cc/#my-libs/lib/XXX e.g. 1ba5703c-c3b9-403e-ac3c-dec836076ce2 
   │   ├── oc_sync_cmd                            : dropbox/location of owncloudcmd  e.g. /usr/bin/owncloudcmd --trust/seafile
   │   ├── oc_webdav_endpoint                     : dropbox/owncloud endpoint e.g. remote.php/webdav/seafile actual version e.g. 4.3.2
   │   └── oc_account_reset_procedure             : dropbox/seafile/webdav_delete 
   │   
   ├── tests
   │   ├── runid                                  : specify runid to attach all the measurements to the one group 
   │   ├── test_name                              : path to test in ``smashbox/lib`` directory 
   │   └── testset                                : id of the test set  
   │
   └── loop                                       : number of loops 
   
</pre>

NEXT, you should create file testrun.config by ``nano testrun.config`` and insert the following file with your configurations

<pre>
{  
    "config" : [
    ],
    "sync_engines" : [
        [
         "engine=owncloud",
         "oc_server=YOUR_SERVER",
         "oc_account_name=YOUR_ACC",
         "oc_account_password=YOUR_PSW",
         "oc_server_folder=YOUR_REMOTE_FOLDER",
         "oc_sync_cmd=YOUR_CMD_DIR",
         "oc_webdav_endpoint=YOUR_WEBDAV e.g. remote.php/webdav",
         "oc_account_reset_procedure=webdav_delete"
        ],
    ],
    "tests" : [
        {
         "runid" : "testrun",
         "test_name" : "performance/test_syncperf.py",
         "testset" : "0"
        }, 
    ],
    "loop" : 1
} 
</pre>

For advanced use, with sniffer, non-native engines, log backup and remote storage, you should use

<pre>
{  
    "config" : [
     "remote=true",
     "sniffer=true",
     "backuplog=true",
     "remote_storage_server=YOUR_SERVER",
     "remote_database=YOUR_DB",
     "remote_storage_user=YOUR_DB_USR",
     "remote_storage_password=YOUR_DB_PSWD",
    ],
    "sync_engines" : [
        [
         "engine=dropbox",
         "oc_server=dropbox",
         "oc_account_name=dropbox",
         "oc_account_password=dropbox",
         "oc_server_folder=dropbox",
         "oc_sync_cmd=dropbox",
         "oc_webdav_endpoint=dropbox",
         "oc_account_reset_procedure=dropbox"
        ],
        [
         "engine=seafile",
         "oc_server=YOUR_SERVER",
         "oc_account_name=YOUR_USR",
         "oc_account_password=YOUR_PSWRD",
         "oc_server_folder=YOUR_LIB",
         "oc_sync_cmd=seafile",
         "oc_webdav_endpoint=4.3.2",
         "oc_account_reset_procedure=seafile"
        ],
        [
         "engine=owncloud",
         "oc_server=YOUR_SERVER",
         "oc_account_name=YOUR_ACC",
         "oc_account_password=YOUR_PSW",
         "oc_server_folder=YOUR_REMOTE_FOLDER",
         "oc_sync_cmd=YOUR_CMD_DIR",
         "oc_webdav_endpoint=YOUR_WEBDAV",
         "oc_account_reset_procedure=webdav_delete"
        ],
    ],
    "tests" : [
        {
         "runid" : "testrun",
         "test_name" : "performance/test_syncperf.py",
         "testset" : "0"
        }, 
        {
         "runid" : "testrun",
         "test_name" : "performance/test_syncperf.py",
         "testset" : "1"
        }, 
    ],
    "loop" : 1
} 
</pre>

and confirm running the test 

``./smashbox-deamon testrun.config``

or 

``./smashbox-deamon YOUR_NAME_FOR_FILE.config``



