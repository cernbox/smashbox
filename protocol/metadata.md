Metadata handling and propagation
=================================

Status: proposal in discussion

References: https://github.com/owncloud/client/issues/3199

X-bit
-----

Sync client propagates the executable permission bit of local files to the server.

For new files:
 * PUT request header: OC-METADATA: mod:x
 * PUT request header: OC-METADATA: `OSX.label:<value>`

For existing files in reaction to local chmod:
 * PROPPATCH
 
Sync client propagates the permission bit from the server to local filesystem:

 * oc:metadata property in PROPFIND: oc:metadata
 * GET response header: OC-METADATA: mod:x, OSX.label:<value>
 


Enabled by capabilities.
 
 
Metadata conflict resolution

Client-side: we attach in the same place as mtime handling. Must be stored in the journal.

Server-side needs plugabble metadata service
 
Does ETAG change when metadata is changed? Parent directory ETAG should change so that all metadata of the files will be listed.






