#!/bin/sh

cp smashbox.conf.template smashbox.conf

sed -i 's/smashdir.*/smashdir = "\/home\/jennifer\/smashbox\/results"/' smashbox.conf
sed -i 's/oc_account_name.*/oc_account_name = "user"/' smashbox.conf
sed -i 's/oc_group_name.*/oc_group_name = "testgroup"/' smashbox.conf
sed -i 's/oc_account_password.*/oc_account_password = "demo"/' smashbox.conf
sed -i 's/oc_server .*/oc_server = "172.18.5.74"/' smashbox.conf
sed -i 's/oc_server_folder.*/oc_server_folder = ""/' smashbox.conf
sed -i 's/oc_ssl_enabled.*/oc_ssl_enabled = False/' smashbox.conf
sed -i 's/oc_server_shell_cmd.*/oc_server_shell_cmd = "ssh root@172.18.5.74"/' smashbox.conf
sed -i 's/oc_server_tools_path.*/oc_server_tools_path = "\/usr\/local\/jenkins\/workspace\/smashbox\/server-tools"/' smashbox.conf
sed -i 's/oc_sync_cmd.*/oc_sync_cmd = "\/usr\/bin\/owncloudcmd --trust"/' smashbox.conf

