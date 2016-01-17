Overview
========

This is a framework for end-to-end testing the core storage functionality of 
owncloud-based service installation. This test framework may be run interactively from a command line, perform continous testing via cron jobs or stress/load testing. It may be easily integrated in testing and QA process.

What we check:
   * sync clients in various scenarios
   * trashbin and versioning
   * sharing of files and folders
   * basic protocol checks and documentation

Features:
* running multiple test scenarios at once, aggregate them in groups by runid and store remotely in the database. Currently supported database is INFLUXDB
* currently supported clients are ownCloud, Seafile, Dropbox
* get details about transfer rates during the sync, distinguishing client to server and server to client syncs
* monitor corruptions and number of synced files in single sync round
* monitor sync time for different scenarios

The goal of this is to:
   * make sure that behavior of the system is understood and not 
     changing unintentionally
   * reproduce difficult bugs more easily
   * a testcase is better way of reporting and documenting bugs 
     or undesired behavior to the developers
   * provide a broad test coverage given a large number of setups and platforms

If you think you see a bug - write a test-case and let others
reproduce it on their systems.

This is work in progress. 

Installation of the database - InfluxDB - STABLE SERVICE
============

Before installing smashbox reporting and analysis tool, and to use all of their capabilities, there is a need of installing InfluxDB to store the results of the working scripts.

You can both install InfluxDB via the instructions from the official repository:

``https://influxdata.com/``

or use the preconfigured source using the docker container:

``sudo docker run --restart=always --net=host --name influxdb -d -p 8083:8083 -p 8086:8086 -e INFLUXDB_HTTP_AUTH_ENABLED="true" -e INFLUXDB_REPORTING_DISABLED="true" tutum/influxdb``

CONFIGURATION EXAMPLE:

Enter the site at which you host the docker, e.g. localhost:8083

``CREATE USER <username> WITH PASSWORD '<password>' WITH ALL PRIVILEGES``

``CREATE DATABASE "smashbox"``

``CREATE USER "demo" WITH PASSWORD 'demo'``

``GRANT ALL/READ/WRITE on smashbox to demo``

Access the database container
``sudo docker exec -it influxdb /bin/bash -c "export TERM=xterm; exec bash"``

Change configuration file, updating
``nano /etc/influxdb/influxdb.conf``

``apt-get upgrade influxdb``

Restart container (after exiting container, on the host)
``docker restart influxdb``

TO BE COMPATILIBLE WITH GRAFANA TEMPLATED DASHBOARDS, YOU NEED TO NAME DATABASE ``smashbox``

Installation of the monitoring graph display - GRAFANA - STABLE SERVICE
============

`` sudo docker run --restart=always --name grafana -i -d -p 3000:3000 grafana/grafana ``

Change the grafana settings inside the image.

`` nano /etc/grafana/grafana.ini ``

Github authentication, configuration and more at:

`` http://docs.grafana.org/installation/configuration/ ``

Check grafana demo for smashbox at http://130.226.137.144:3000/, user:password >> demo:demo 
You can also export the DASHBOARDS directly from there and install them at your instance! Just remember to set the following config at Data Sources section:

Name smashbox
Database smashbox

Please do it before you will install your DASHBOARD!

`` More at https://www.youtube.com/watch?v=QhhwzgAKd9U ``

Installation of prerequisites
============

Note: Currently this framework works on Unix-like systems only. Windows port is needed.

``docker run -d --restart=always --name smashbox mrow4a/smashbox:latest``

or sometimes

``docker run -d --restart=always --name smashbox --net=host mrow4a/smashbox:latest``

``sudo docker exec -it smashbox /bin/bash -c "export TERM=xterm; exec bash"``

DOCKER CONTAINER IS ALREADY INSTALLED WITH ownCloud client and other prerequisites, you only need to specify the configuration file and run tests.

IF YOU WANT TO USE OUTSIDE THE mrow4a/smashbox container follow instructions:
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

``apt-get install python-numpy``

Clone git repository into your local ``smashbox`` directory.

``git clone https://github.com/mrow4a/smashbox.git``

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

Make also sure that under ``/devices/`` in your seafile account, all the devices are removed. Before running, make sure that folder ~/smashdir is empty

If you will skip this step, your seafile will freeze on ``Starting to download ...``

NOTE: If your seafile hangs during the first run and you performed first steps, take ctrl+C, exit and restart container, your seafile should now perform test correctly. Please also check if at your seafile account, in the panel DEVICES, there are listed recently 3 devices(or different number depending on test, usually worker0, worker1, boss -> 3) and they have attached your library. 

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
   │   ├── oc_sync_cmd                            : dropbox/location of owncloudcmd  e.g. /usr/bin/owncloudcmd --
   │   ├── oc_ssl_enabled                          : true/false -- specify is server uses SSL
   │   ├── oc_webdav_endpoint                     : dropbox/owncloud endpoint e.g. remote.php/webdav/seafile actual version e.g. 4.3.2
   │   └── oc_account_reset_procedure             : dropbox/seafile/webdav_delete 
   │   
   ├── tests
   │   ├── runid                                  : specify runid to attach all the measurements to the one group 
   │   ├── test_name                              : path to test in ``smashbox/lib`` directory 
   │   └── testset                                : id of the test set  
   │
   ├── ensure_net_qos		          : secure against situation when you have very bad network condition on the test machine
   ├── timeout	                                  : define how long it will sync till it kills the process
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
         "oc_account_reset_procedure=webdav_delete",
         "oc_ssl_enabled=false",
        ],
    ],
    "tests" : [
        {
         "runid" : "testrun",
         "test_name" : "performance/test_syncperf.py",
         "testset" : "0"
        }, 
    ],
    "loop" : 1,
    "ensure_net_qos" : 10,
    "timeout" : 3600,
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
         "oc_account_reset_procedure=webdav_delete",
         "oc_ssl_enabled=false",
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
    "loop" : 1,
    "ensure_net_qos" : 10,
    "timeout" : 3600,
} 
</pre>

and confirm running the test 

``./smashbox-deamon testrun.config``

or 

``./smashbox-deamon YOUR_NAME_FOR_FILE.config``


