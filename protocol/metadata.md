Metadata handling and propagation
=================================

Status: proposal in discussion

References: https://github.com/owncloud/client/issues/3199

X-bit
-----

Sync client propagates the executable permission bit of local files to the server.

For new files:
 * PUT request header: OC-METADATA-XBIT:1

For existing files in reaction to local chmod:
 * PROPPATCH
 

Sync client propagates the permission bit from the server to local filesystem:

 * oc:metadata property in PROPFIND: oc:metadata=XBIT
 * GET response header: OC-METADATA-XBIT:1
 
 





