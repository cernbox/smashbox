#!/bin/bash
dropboxes=""
home_dir=$1
for var in "${@:2}";
do
    dropboxes+="$var "
done
for dropbox in $dropboxes
do
    HOME=$home_dir
    if ! [ -d "$dropbox" ]
    then
        mkdir "$dropbox" 2> /dev/null
        ln -s ".Xauthority" "$dropbox/" 2> /dev/null
    fi
    HOME="$dropbox"
    $home_dir/.dropbox-dist/dropboxd 2> /dev/null &
done
