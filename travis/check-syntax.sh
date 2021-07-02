#!/bin/bash

exitCode=0
for FILE in $(find ../ -name "*.py" -type f -not -path "*/.git/*")
do
    errors=$(python travis/check-syntax.py $FILE)
    if [ "$errors" != "" ]
    then
        echo -n "${errors}"
        exitCode=1
    fi
done

echo ""

exit $exitCode
