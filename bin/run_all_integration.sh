#!/bin/bash

if [ -z "$1" ] ; then
    echo "Running from etc/smashbox.conf locally"

    if [ ! -f requirements.txt ]; then
        echo "bin/smash not found in this directory, cd to smashbox root dir then run this script"
        exit 1
    fi

    CMD="bin/smash -v -a"
else
    echo "Running from in docker again server ip $1"
    CMD="docker run -e SMASHBOX_URL=$1 -e SMASHBOX_USERNAME=admin -e SMASHBOX_PASSWORD=admin -e SMASHBOX_ACCOUNT_PASSWORD=admin owncloud/smashbox"
fi

$CMD lib/test_basicSync.py && \
$CMD lib/test_concurrentDirRemove.py && \
$CMD lib/test_nplusone.py && \
$CMD lib/oc-tests/test_reshareDir.py && \
$CMD lib/oc-tests/test_shareDir.py && \
$CMD lib/oc-tests/test_shareFile.py && \
$CMD lib/oc-tests/test_shareGroup.py && \
$CMD lib/oc-tests/test_shareLink.py && \
$CMD lib/oc-tests/test_sharePermissions.py && \
$CMD lib/owncloud/test_shareMountInit.py && \
$CMD lib/owncloud/test_sharePropagationGroups.py && \
$CMD lib/owncloud/test_sharePropagationInsideGroups.py
