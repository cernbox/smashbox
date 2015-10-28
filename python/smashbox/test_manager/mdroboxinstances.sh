#!/bin/bash
dropboxes=""
for var in "$@"
do
    dropboxes+="$var "
done
for dropbox in $dropboxes
do
    HOME="/home/$USER"
    if ! [ -d "$dropbox" ]
    then
        mkdir "$dropbox" 2> /dev/null
        ln -s ".Xauthority" "$dropbox/" 2> /dev/null
    fi
    HOME="$dropbox"
    /home/$USER/.dropbox-dist/dropboxd 2> /dev/null &
done