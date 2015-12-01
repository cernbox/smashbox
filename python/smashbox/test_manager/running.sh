#!/bin/bash
PROCESS=$1
PIDS=`ps cax | grep $PROCESS | grep -o '^[ ]*[0-9]*'`
if [ -z "$PIDS" ]; then
	if [ -z "$2" ]
	then    
  		val="Process not running"	
  		echo $val
	else
		if [ "$2" = "reboot" ]; then
			shutdown -r now 
		fi
	fi
else
  	for PID in $PIDS; do
    	echo $PID
  	done
fi