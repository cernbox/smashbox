#!/usr/bin/env bash

set -o errexit # bail out on all errors immediately

function error() {
    echo ERROR: $1
    exit -1
}

ACCOUNT=$1

if [ -z "$ACCOUNT" ]; then

echo "Missing argument: account_name"
exit -2

fi

mkdir -p /var/tmp/report

cd /var/tmp/report

/root/smashbox/bin/smash  -q /root/smashbox/lib/migration/scan_propfind.py -c /root/smashbox/lib/migration/scan.conf -o oc_account_name=$ACCOUNT -o oc_server=eoshome & PID_SMASH_1=$!
/root/smashbox/bin/smash  -q /root/smashbox/lib/migration/scan_propfind.py -c /root/smashbox/lib/migration/scan.conf -o oc_account_name=$ACCOUNT -o oc_server=eosuser & PID_SMASH_2=$!

# wait for both subprocess to finish but bail out if any of the returned an error

wait $PID_SMASH_1 || exit -2
wait $PID_SMASH_2 || exit -2

# CHECK THE METADATA -- ALL SHOULD BE PROPERLY ALIGN (PLACEHODLER VALUES ARE EXCEPTION)

diff report.propfind.${ACCOUNT}.eoshome.txt report.propfind.${ACCOUNT}.eosuser.txt || error "metadata mismatch"

# CHECK FOR REPEATED METADATA VALUES -- SHOULD BE NONE

X=`comm -12 report.d-etags.${ACCOUNT}.eosuser.txt  report.d-etags.${ACCOUNT}.eoshome.txt`

if [ -n "$X" ]; then 
echo $X
error "Repeated directory etags found" 
fi

X=`comm -12 report.d-ids.${ACCOUNT}.eosuser.txt  report.d-ids.${ACCOUNT}.eoshome.txt`

if [ -n "$X" ]; then 
echo $X
error "Repeated directory ids found" 
fi

X=`comm -12 report.f-ids.${ACCOUNT}.eosuser.txt  report.f-ids.${ACCOUNT}.eoshome.txt`

if [ -n "$X" ]; then 
echo $X
error "Repeated file ids in found" 
fi

echo OK: ${ACCOUNT}
