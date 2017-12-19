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
   │   ├── test_nplusone.py			
   │   └── ...  			        
   ├── protocol/                                : sync protocol tests and documentation
   ├── python/                                  : implementation of tools and API library for tests
   │   └── smashbox/utilities                   : here is the utilities used directly in the test-cases
   ├── server/                                  : server-side procedures used in the tests
   ├── client/                                  : owncloud client helpers 
   │   └── compile-owncloud-sync-client*        : 
   └── README                                   : this file
   
</pre>

Supported OSes
============

Requires:
 * python 2.7+
 * pycurl

Linux
-----

This framework should work out-of-the-box on any recent Linux
which supports python2.

Sync clients will usually be in the PATH.

MacOSX
-------

Dependency installation via pip (example):
  * sudo pip install pycurl

You may need to run the smashbox executable by calling python
interpreter directly like this:

python bin/smash

Location of sync clients:

 * /Applications/cernbox.app/Contents/MacOS/cernboxcmd
 * /Applications/owncloud.app/Contents/MacOS/owncloudcmd
 
Windows
--------

Dependency installation via pip (example):
 * c:/Python27/python.exe -m pip install pycurl

 You may need to call python interpreter directly:

c:/Python27/python.exe bin/smash

Location of sync client may be configured like this:

 * oc_sync_cmd = ['C:\Program Files (x86)\cernbox\cernboxcmd.exe',"--trust"]

Installation
============

Clone git repository into your local ``smashbox`` directory.

Copy the etc/smashbox.conf.template into etc/smashbox.conf

Note: a helper shell script, makeconfig, has been added to the etc directory. 
Edit this file to make some of the more common configuration changes and then run the script.  
This will create a local smashbox.conf file.

Set the oc_sync_cmd to the location of the owncloud command-line
client (see client/compile-owncloud-sync-client if you don't have one
yet compiled).

Set the oc_account_password.

Otherwise the default configuration should work out-of-the-box if you
run the smashbox tests locally on the owncloud server. You should try
that first (on the TEST server instance).

Support has been added for the provisioning API which creates a dependency on the pyocclient repo.

To install the library, run the following after checking out your branch:

pip install -r requirements.txt

If you want to use a local copy of pyocclient, you can add the following to your shell environment:

export PYTHONPATH=/local/path/to/pyocclient/repo/branch

and clone git repository into your local ``pyocclient`` directory.

First test runs
===============

When you run a test several workers (clients) are started in parallel
locally and access owncloud server according to the test-case
scenario. The test-case specifies which actions happen simultaneously.

Examples:

    # help on all available options
    bin/smash --help

    # basic test
    bin/smash lib/test_basicSync.py
    
    # run a test with different paremeters
    bin/smash -o nplusone_nfiles=10 lib/test_nplusone.py
    
    # run all tests - print summaries only
    bin/smash --quiet lib/test_*.py

You will find main log files in ~/smashdir/log* and all temporary files and detailed logs for each test-case in ~/smashdir/<test-case>


Different client/server
=======================

Make sure you can passwordlessly ssh to the server node (only for some admin tasks like creating accounts)
You will need to set oc_server, oc_server_shell_cmd. 

If you don't keep the same path on the server and the client to the smashbox git repository clone then you will need to set oc_server_tools_path.

As of version x.x, the provisioning API is used for user management on the server so this is no longer needed.

Adding new tests
================

Simply add new tests to smashbox/lib. If you have specific tests which are not generally applicable or which belong to the same functional category it is best to store them in a subdirectory, e.g. smashbox/lib/oc-tests.

If you need to add new utilities then add a module in smashbox/python/smashbox/utilities.


Design criteria for this testing software
=========================================

  - test scripts with minimal code clutter
  - possible to run individual test scripts or the whole suite at once
  - convenient run environment for systematic and ad-hoc testing
  - easy and flexible configuration
  - easy to add and run tests in an additional lib
  - possibility to extend with cluster mode (distributed workers)


Test configuration details
==========================

Configuration may be set globally in smashbox/etc/smashbox.conf,
passed as a command line option to commands or hardcoded in the code
of an individual test. This is also the priority order - whatever is
defined last wins.

In the future we would like to add other possibilities
(lib/smashbox.conf, $SMASHBOX_CONF file if defined)

Local working directories keep temporary files, local sync folders, etc. General structure (some elements of the path may be ommited, others may be transformed)::

     <smashdir>/<rundir>/<testname>

Server test accounts follow this general naming scheme (some elements may be ommited, others may be transformed) ::

    smash-<runid>-<collection>-<testname>
   

Organization of test directories
----------------

Consider running an simple test::

    smash smashbox/lib/test_nplusone.py

If workdir_runid_enabled option is enabled then local working directory will be everytime different (and unique)::
 
    <runbasedir>/test_nplusone-<runid>

The format of <runid> identifier is defined by the runid option.

Otherwise the local working directory will be the same (and cleaned-up before running the test)::

    <runbasedir>/test_nplusone

If oc_account_runid_enabled is enabled then the test account on the server will be everytime different (and unique)::

    smash-nplusone-<runid>

Otherwsie the test account on the server will be everytime the same (and will be cleaned-up before running the test)::

    smash-nplusone

The account_cleanup_procedure defines how the account is cleaned-up before running the test. These procedures are defined in smashbox/python/smashbox.


