#!/bin/bash
PROCESS=$1
PIDS=`ps cax | grep $PROCESS | grep -o '^[ ]*[0-9]*'`
if [ -z "$PIDS" ]; then
  val="Process not running"	
  echo $val
else
  for PID in $PIDS; do
    echo $PID
  done
fi