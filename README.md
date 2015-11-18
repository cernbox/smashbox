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

Installation
============

Note: Currently this framework works on Unix-like systems only. Windows port is needed.

Login as root, if you are willing to use sniffer, if not, you can stay as normal user. 

``sudo su``

`` cd ``

Clone git repository into your local ``smashbox`` directory.

To install the library, run the following after checking out your branch:

pip install -r requirements.txt

If you want to use a local copy of pyocclient, you can add the following to your shell environment:

export PYTHONPATH=/local/path/to/pyocclient/repo/branch

and clone git repository into your local ``pyocclient`` directory.

If you are willing to use ``dropbox``, you should go to parent dir using ``cd``,

run ``smashbox/bin/smash -o oc_account_password=dropbox -o engine=dropbox --testset 0 smashbox/lib/performance/test_syncperf.py``

If you are on the text-based system, information about accessing the link and enabling dropbox client will appear. If it is desktop system, it will open the dropbox desktop client so that you could enter credentials for the dropbox account.

For Seafile client, first you need to set up the certificates on ubuntu, because the latest CLI client uses http protocol for synchronization. If you use https on the Seafile server side, you can't connect to the server from a Debian/Ubuntu machine using this CLI client:

<pre>
sudo mkdir -p /etc/pki/tls/certs
sudo cp /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt
sudo ln -s /etc/pki/tls/certs/ca-bundle.crt /etc/pki/tls/cert.pem
</pre>

If you will skip this step, your seafile will freeze on ``Starting to download ...``

NEXT, you shoudl create file testrun.config by ``nano smashbox/testrun.config`` and insert the following file

<pre>
{  
    "config" : [
     "remote=true",
     "sniffer=true",
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
         "oc_server=https://seacloud.cc/",
         "oc_account_name=YOUR_USR",
         "oc_account_password=YOUR_PSWRD",
         "oc_server_folder=YOUR_LIB",
         "oc_sync_cmd=seafile",
         "oc_webdav_endpoint=4.3.2",
         "oc_account_reset_procedure=seafile"
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

or just 

{  
    "config" : [
     "remote=false",
     "sniffer=false",
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

and confirm running the test 

``smashbox/smashbox-deamon smashbox/testrun.config``

First test runs
===============

TO BE CONTINUED...


