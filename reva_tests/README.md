# REVAD Smashbox Tests

This folder contains some tests to run agains REVA.

This is the minimal smashbox.conf to run REVA tests:

```
smashdir = "/tmp/smashdir"

oc_account_name='.'
oc_account_password='doesntmatter'
oc_sync_cmd='./bin/smash'

rundir_reset_procedure = "delete"
runid=None
workdir_runid_enabled=True
oc_account_reset_procedure = "keep"

reva_tests_username = 'labradorsvc'
reva_tests_password = 'bar'
reva_tests_reva_cli_binary = '/root/go/src/github.com/cernbox/reva/reva-cli/reva-cli'

oc_server = ''
```

The best way to run the test is the following:

```
/root/smashbox/bin/smash --keep-going --drop-passed -c /etc/smashbox/smashbox.conf /root/smashbox/reva_tests/revad_corruption.py
```


These are the definitions of the tests running against a revad server:

### revad_corruption
This tests creates samples files with the same block size REVA creates the chunks (3MiB) and uploads
the files to the revad daemon.
Once files are uploaded, they are downloaded and analysed for possible corruptions comparing the original md5 checksum
and the new one.

