# OC Sync Protocol

Document Authors: Jakub.Moscicki@cern.ch, Klaas Freitag <freitag@owncloud.com>

Document Date: 2014-08-21

This document is part of cernbox project (AGPL license).

## Introduction

This is an attempt to describe the protocol used by owncloud desktop client for syncing files.

Applies to owncloud client starting version 1.6 and owncloud server 6 and 7. We are deliberately omitting older implementation which require obsolete methods (such as PROPPATCH to set mtime after PUT).

Owncloud desktop client uses a mix of HTTP REST calls and WEBDAV with few header extentions and conventions.

Minimalistic doc style. Work in progress.

## Authorization

Unless it is specified explicitly all calls must be authorised (https or http
with authorization header).

With every HTTP request, the client sends a BasicAuth header
containing user and password as described in RFC #2617
(https://www.ietf.org/rfc/rfc2617.txt).  If the authentication was
successful, the server returns a session cookie that is stored by the
client. If a valid session cookie exists then it is sent in addition to a
Basic Auth credentials. The server may use the session cookie, but if
that fails, server can fall back to the BasicAuth header.

The users password in the BasicAuth header is not encrypted. Hence this protocol
relies on https for providing secure communication channel.

Authorization header:

    Authorization: Basic BASE64(username:password)


## Special Request Headers

Standard and non-standard headers which have special significance.

### Dealing with conflicts

- ETag
- If-Match

### Chunk transfer

- OC-Total-Length
- OC-Chunked

TODO: also range requests to resume downloads


### Metadata propagation

- X-OC-Mtime

## Special Response Headers

- ETag
- X-OC-MTime
- OC-FileId

## REST API

### Server status

Syntax:

    GET /status.php HTTP/1.1
    Authorization: none

Reponse: 200

Response body:

Static information about the server version in JSON format.

Response example for owncloud 7.0.1:

    {"installed":"true","version":"7.0.1.1","versionstring":"7.0.1","edition":""}

### Capabilities Call

Client can query the server to get a list of available server capabilities. This is an authenticated
request.

Syntax:

    GET /ocs/v1.php/cloud/capabilities?format=json

Response: 200

Response body:

Static information about server capabilities delivered through an OCS call. This is the 
prefered way of getting information about the server capabilities.

Response Example for ownCloud 8.0.x:

    {
        "ocs": {
            "data": {
                "capabilities": {
                    "core": {
                        "pollinterval": 60
                    }, 
                    "files": {
                        "bigfilechunking": true, 
                        "undelete": true, 
                        "versioning": true
                    }
                }, 
                "version": {
                    "edition": "", 
                    "major": 8, 
                    "micro": 7, 
                    "minor": 0, 
                    "string": "8.0.7"
                }
            }, 
            "meta": {
                "message": null, 
                "status": "ok", 
                "statuscode": 100
            }
        }
    }

Explanation of the capabilities:

* `pollinterval`: Interval to poll for server side changes (unused)
* `bigfilechunking`: Flag if server supports big file chunking
* `undelete`: Flag if server supports big file trash
* `versioning`: Flag if server supports big file versioning
* `version`: detailed server version information
* `meta`: ocs meta information

Source code reference: client/src/libsync/capabilities.cpp (https://github.com/owncloud/client/blob/master/src/libsync/capabilities.cpp)

## WEBDAV

Standard webdav request/response conventions apply.

Namespace for non-standard properties: `http://owncloud.org/ns`

### Restrictions and limitations

#### ETag Format

There are no format restrictions on the ETag value. However, for historical reasons the following deprecated rules are valid for the value of the ETag header:

 - if ETag header value is enclosed in double quotes ("double-quoted") then client should strip off the quote characters
 - if ETag header value contains the word then "-gzip", client should remove that with no replace. Ref http://github.com/owncloud/client/issues/1195 

#### Properties

In the response body the value of resourcetype property MUST NOT contain whitespaces (implementation as of owncloud client 1.5):

        <d:resourcetype><d:collection/></d:resourcetype>

#### Headers

PROPFIND Depth:infinity is not supported: client will try this for compatibility with older code  but server may choose to return 501 (NotImplemented).

### Quota Check Call

Client displays user quota information. For that it does a PROPFIND call to the root of the 
user space on the webdav server. Quota is reported per account (or per quota node) defined on the storage server. The result of this query will be the same for all directories (URI part of the request) which belong to the same account (or quota node).

Syntax:

	> PROPFIND /remote.php/webdav/ HTTP/1.1
	Depth: 0

	<?xml version="1.0" ?>
	  <d:propfind xmlns:d="DAV:"><d:prop>
	      <d:quota-available-bytes/>
	      <d:quota-used-bytes/>
	  </d:prop></d:propfind>

Response: 207

Reponse body example:

    < PROPFIND

    <?xml version='1.0' encoding='utf-8'?>
    <d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns" xmlns:oc="http://owncloud.org/ns">
      <d:response>
        <d:href>/remote.php/webdav/</d:href>
        <d:propstat>
          <d:prop>
            <d:quota-available-bytes>14883876864</d:quota-available-bytes>
            <d:quota-used-bytes>592610518</d:quota-used-bytes>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
      </d:response>
    </d:multistatus>
    

### Connection Validation Call

To detect if there is still a vital uplink to the server, client does a PROPFIND request
to the top level directory to query the last modified timestamp. 

This call needs working authentication and is used to verify that authentication and the
network connection in general is still up and running. Depending on the result of this call
client goes to offline mode or opens the authentication dialog to ask for new password.

Syntax:

    > PROPFIND /remote.php/webdav/ HTTP/1.1
    Depth: 0

    <?xml version="1.0"?>
     <d:propfind xmlns:d="DAV:"><d:prop>
       <d:getlastmodified />
     </d:prop></d:propfind>

Reponse: 207

Response body example:

    < PROPFIND

    <?xml version='1.0' encoding='utf-8'?>
    <d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns" xmlns:oc="http://owncloud.org/ns">
      <d:response>
        <d:href>/remote.php/webdav/</d:href>
        <d:propstat>
          <d:prop>
            <d:getlastmodified>Mon, 07 Sep 2015 13:30:52 GMT</d:getlastmodified>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
      </d:response>
    </d:multistatus>

This call only happens to the server top directory.

### Modification Check on Top-level Directory

FIXME: this section and its example is plain wrong and needs reviewing

To detect changes of data on the server repository client issues stat-like calls to the 
top level directory of a sync connection to request the last modification timestamp on a regular basis. 

Syntax:
    > PROPFIND /remote.php/webdav/ HTTP/1.1
    Depth: 0

    <?xml version='1.0' encoding='UTF-8'?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:getetag/>
      </d:prop>
    </d:propfind>
    
Reponse: 207

Response body example:

    < PROPFIND

    <?xml version='1.0' encoding='utf-8'?>
    <d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns" xmlns:oc="http://owncloud.org/ns">
      <d:response>
        <d:href>/remote.php/webdav/</d:href>
        <d:propstat>
          <d:prop>
            <d:getetag>"55ed918c28ac9"</d:getetag>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
      </d:response>
       <d:response>
        <d:href>/remote.php/webdav/%d7%91%d7%a2%d7%91%d7%a8%d7%99%d7%aa-.txt</d:href>
        <d:propstat>
          <d:prop>
            <oc:id>00004227ocobzus5kn6s</oc:id>
            <oc:permissions>RDNVW</oc:permissions>
            <d:getetag>"ed3bcb4907f9ebdfd8998242993545ba"</d:getetag>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
      </d:response>
    </d:multistatus> 
        
Client returns with a listing of all top level files and directories with their meta data.
Comparing the ETag of the toplevel directory with the one from the previous call, client 
can detect data changes on the server. In case the top level ETag changed, client can 
traverse the changed server tree by the ETag information.

### List directory

List directory _path_ and return mtime, size, type, etag and file id.

Syntax:

    > PROPFIND /remote.php/webdav/Test%20Folder HTTP/1.1
    Depth: 1

    <?xml version='1.0' encoding='UTF-8'?>
    <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
      <d:prop>
        <d:resourcetype/>
        <d:getlastmodified/>
        <d:getcontentlength/>
        <d:getetag/>
        <oc:id/>
        <oc:downloadURL/>
        <oc:dDC/>
        <oc:permissions/>
        <oc:size/>
      </d:prop>
    </d:propfind>
    
Response: 207

Response body: see restrictions and limitations paragraph

Response body example:

    < PROPFIND

    <?xml version='1.0' encoding='utf-8'?>
    <d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns" xmlns:oc="http://owncloud.org/ns">
      <d:response>
        <d:href>/remote.php/webdav/a%20new%20folder/</d:href>
        <d:propstat>
          <d:prop>
            <oc:id>00004609ocobzus5kn6s</oc:id>
            <oc:permissions>RDNVCK</oc:permissions>
            <oc:size>2087</oc:size>
            <d:getetag>"55ed9bc2ea689"</d:getetag>
            <d:resourcetype>
              <d:collection/>
            </d:resourcetype>
            <d:getlastmodified>Mon, 07 Sep 2015 14:14:26 GMT</d:getlastmodified>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
        <d:propstat>
          <d:prop>
            <d:getcontentlength/>
            <oc:downloadURL/>
            <oc:dDC/>
          </d:prop>
          <d:status>HTTP/1.1 404 Not Found</d:status>
        </d:propstat>
      </d:response>
        <d:response>
        <d:href>/remote.php/webdav/a%20new%20folder/Test.txt</d:href>
        <d:propstat>
          <d:prop>
            <oc:id>00004610ocobzus5kn6s</oc:id>
            <oc:permissions>RDNVW</oc:permissions>
            <d:getetag>"99cf2191bbd9b79f99d9a1bfef015947"</d:getetag>
            <d:resourcetype/>
            <d:getlastmodified>Mon, 07 Sep 2015 14:09:47 GMT</d:getlastmodified>
            <d:getcontentlength>17</d:getcontentlength>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
        <d:propstat>
          <d:prop>
            <oc:downloadURL/>
            <oc:dDC/>
          </d:prop>
          <d:status>HTTP/1.1 404 Not Found</d:status>
        </d:propstat>
      </d:response>
      <d:response>
        <d:href>/remote.php/webdav/a%20new%20folder/tagfrei_wald.txt</d:href>
        <d:propstat>
          <d:prop>
            <oc:id>00004613ocobzus5kn6s</oc:id>
            <oc:permissions>RDNVW</oc:permissions>
            <d:getetag>"8d9b7283af7592105a28e2654a21a81e"</d:getetag>
            <d:resourcetype/>
            <d:getlastmodified>Mon, 07 Sep 2015 14:14:26 GMT</d:getlastmodified>
            <d:getcontentlength>2070</d:getcontentlength>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
        <d:propstat>
          <d:prop>
            <oc:downloadURL/>
            <oc:dDC/>
          </d:prop>
          <d:status>HTTP/1.1 404 Not Found</d:status>
        </d:propstat>
      </d:response>
    </d:multistatus>
    
Explanation of the `PROPFIND` result attributes:

* `oc:id`: FileID of file or directory
* `oc:permissions`: Permissions of the file or directory (see: https://github.com/owncloud/client/blob/master/doc/architecture.rst#server-side--permissions)
* `oc:size`: Size in bytes of file or directory (recursive size of the directory tree)
* `oc:getetag`: ETag 
* `oc:downloadURL`: Direct download URL (extension)
* `oc:dDC`: Direct download cookie (extension)
* `d:resourcetype`: either sub element `collection` or empty for files
* `d:getlastmodified`: Last modified date of the resource
* `d:getcontentlength`: size in bytes

More details on custom webdav properties : https://github.com/owncloud/client/blob/master/doc/architecture.rst#custom-webdav-properties

    
### Create directory

Syntax: 

    MKCOL /remote.php/webdav/new_directory

Response: 201

Request Custom Header: None

Response Custom Header:

`OC-FileId`: The fileId of the new directory.

Specific error code handling: None

### Move file or directory


Syntax: 

    MOVE /remote.php/webdav/old_name
    Destination: /remote.php/webdav/new_location/new_name

Response: 201

Request Custom Header: None

Response Custom Header:

`OC-FileId`: The fileId of the new directory.

Specific error code handling: None

## HTTP

### Remove a file or directory

Syntax:

    DELETE /remote.php/webdav/file_or_directory

Response: 204

Example:

    DELETE https://mycomputer/remote.php/webdav/documentation

Request Custom Header: None

Response Custom Header:

None.

Specific error code handling:

* `403` - No permission to remove the file (directory) on the server (e.g. shared with read-only permissions). The client will re-download a locally deleted file (directory) in a subsequent sync run.
* `404` - Not considered an error, because the file (directory) is already gone.


### File Download 

Client downloads files from the ownCloud server by HTTP GET requests via
the WebDAV route on the server. Since GET requests do not have the same
limitations that PUT requests have (file size limitation) there is no
chunking required for downloads.

Syntax:

   GET /remote.php/webdav/file

Response: 201

Example:

    GET https://mycomputer/remote.php/webdav/cheaper.jpg

Request Custom Header:

Optional: Range header - set if the client detects that the download can be resumed.

Response Custom Header:

`Last-Modified`: Thu, 03 Sep 2015 13:50:22 GMT - the last modification time
                 of the resource in question. Use to update the meta data
                 of the file in the sync engine.
                 
`ETag`:          `"6c17343130f542a7410569a5f0c88abc"` - the current ETag of
               the file. Note that the ETag may be enclosed in quotes
               for historical reason.

Specific error code handling:

* `416`: The request sent an range header that did not fit. Receiving 416 means that the request has to be tried again without range header.
* `404`: The file to download was meanwhile deleted on the server


### Plain File Upload 

File upload to the server happens through HTTP PUT. If the file size exceeds a certain size, the file uploads happens through so
called "big file chunking", see next chapter.

Syntax:

    PUT remote.php/webdav/file

Response: 201

Example:

    PUT https://mycomputer/remote.php/webdav/documentation/mybook.txt

Request Custom Header:

`If-Match`: ETag to be overwritten by this PUT. Server refuses to replace the file if the ETag on the server is different.

`OC-ASync`:        1  - Allow a asynchronous file assembly on the server. This is an optional server feature. Reference: https://github.com/owncloud/core/issues/12097

`OC-Chunk-Size`:   longint - Size of a chunk in bytes. Ignored chunking is not happening

`OC-Total-Length`: longint - File size in bytes

`X-OC-Mtime`:      longint - time stamp in seconds since 1.1.1970
                           Server sets this value as modification time of
                           the new file.

Response Custom Header:

`X-OC-MTime:    accepted` - indicates that the server updated the files
                          modification time. If that is not set, client
                          is supposed to send a subsequent PROPSET to set
                          the files modification time.
                          
`OC-FileId:     00004551ocobzus5kn6s` - the file id of the file

`ETag:          "17e18721bf7133b5449f18b8a2b1dae1"` - the new ETag of the file.
                                                    client stores the new ETag
                                                    in the sync journal

Specific error code handling:

`403 `: client tried to overwrite a shared file without permission.
      The client will try to recover the file from server in a subsequent
      sync run and create a conflict file with the local changes.


### Chunked File Upload 

Note: new generation fo chunked upload is under development and it is described here: 
https://github.com/cernbox/smashbox/blob/master/protocol/chunking.md

If the file size exceeds a certain size, the file uploads happens
through so called "big file chunking". The file is split into chunks
of equal sizes and each chunk is transfered to the server through its
own PUT request. Client performs HTTP PUT requests to a pseudo URI
based on the file name, as described below.

Client performs PUT requests to a special name for each chunk.
The name consists of four components appended ot the original name of
the file with the character '-' between them.

The first component is the constant term "-chunking-". That is appended
by a number which is called 'transfer id'. The transfer Id is used to
identify the individual file transfer on server side and thus is supposed
to be unique enough to avoid collisions on the server.
The third component is a number indicating the overall amount of chunks
the transfer is consisting of. The last component is the number of
the current chunk, starting with zero. The sequence number indicates
the sequence how the server is supposed to reassemble the original file.


Syntax (N chunks, i-th chunk, transferId):

   PUT /remote.php/webdav/file-chunking-transferId-N-i

Response: 201

Example:

    PUT https://mycomputer/remote.php/webdav/large.tgz-chunking-4273312896-15-0

Request Custom Header:

All header described in "Plain File Upload" and in addition:

`OC-Chunked:        1`  - indicates chunked file transfer.

Response Custom Header: 

No custom headers for responses to first and intermediate chunks
requests.  For the response to the final chunk request, all response
headers described in "Plain File Upload" apply.

Note: The final chunk is not neccessarily the one with the highest
sequence number. The final chunk is the one which makes up for the
complete file on the server (this distinction becomes important when
for example intermediate chunk upload fails and is retried later).
Server must add the custom headers to the response of the final chunk
to indicate the fact that the chunked file transfer is now complete.
For the client that means that it may keep sending chunks as long
as it hasn't detected the response headers for the final chunk.

`OC-ErrorString` - Optional header that returns the original error message
of the server in case something went wrong.

`OC-Finish-Poll` - Optional header in case server and client support asnychronous
                   handling of the long running file assembly process. In this
                   case, server returns 202 in reply to the chunk request. Client
                   reads an URL from the optional header OC-Finish-Poll which is
                   polled regularly by client until it becomes valid and contains
                   the meta data of this transfer, ie. ETag etc. Note that this
                   is not yet implemented on the ownCloud server. Reference: https://github.com/owncloud/core/issues/12097

Specific error code handling:

`403`: client tried to overwrite a shared file without permission.
       The client will try to recover the file from server in a subsequent
       sync run and create a conflict file with the local changes.


`412`:  Precondition failed: the transfer attempted to overwrite a file
        which was changed on the server meanwhile, which was not allowed.
        Client needs to mark the file for a new sync in the a subsequent
        sync run that is started.


`202`:  Async file assembly started, see description for OC-Finish-Poll custom
        header.

Other error conditions:

* client checks if the local file (which is currently uploaded) was removed.
* client checks if the local file (which is currently uploaded) was changed
  by comparing the actual modification time with the one that was stored
  during the discovery phase.

Resuming of Transfer:

Client can not resume the upload of single chunks. If a certain chunk upload
fails, client will repeat it and transfer the full chunk again.

# Checksumming extensions

Checksumming has been implemented in CERNBOX 1.7.2 client and it is currently integrated into owncloud sync client 2.x releases. It follows this specification:

https://github.com/cernbox/smashbox/blob/master/protocol/checksum.md


# OC Sync Semantics

## New development ideas

Currently under discussion:

https://dragotin.wordpress.com/2015/06/22/owncloud-chunking-ng/
https://dragotin.wordpress.com/2015/07/10/owncloud-chunking-ng-part-2-announcing-an-upload/
https://dragotin.wordpress.com/2015/11/13/owncloud-chunking-ng-part-3-incremental-syncing/


## Lifecycle and semantics of FileId vs path vs etag

The FileId is suitable for tracking the server-side moves but it is not suitable
for making permanent one-to-one associations of remote and local paths for purposes
such as avoiding case clashes with case-insensitive clients.

This is because the FileId associated with a path may change in time. For example,
if you delete a file/directory on the server and then recreate it with the same name
-- it will get a new FileId. So FileId really acts as an inode number and it should
be assumed that it may change for the same path at any time. Implementation of another
behaviour (be it in the database or directly on storage) is impractical. So current
behaviour is probably a good candidate to become formally part of the owncloud sync
protocol.

Although the same path may have different values of FileId over the course of its
lifetime, it is guaranteed that FileIds never repeat. The remote move detection is
thus based on the fact that the set of server changes (as detected by the client)
contains a new path which is associated with a previously known FileId.

The client remembers the old path associated with the FileId and thus may propagate
the remote move by performing a local move from old path to new. It is up to the
client to track local moves, so it should be able to propagate the remote move
correctly even if the same local path was also moved at the same time.

The sync protocol concerns keeping *paths* consistent between the clients and the
server: when a change is detected then it is propagated to the corresponding path
on the other side.

Detection of local path modifications is up to the client. Etag is used by the clients
to understand if a path has changed on the server. When a path is changed on the server
it's Etag will get a new, unique value. Etag must have a property such that if there
is a change of content of a path, it is guaranteed that the new value of the Etag will
not be equal to any previous Etag values that a client may have seen in the past.
Otherwise changes could remain undetected if paths were renamed or moved. UUID is a
good Etag because it is unique across the entire namespace. An integer per file version
number (0,1,2,…) which is incremented on every update of that file if not a good Etag.

A strong checksum on file content is the most efficient Etag because it allows to ignore
the updates which do not change the content. For directories: the UUID is a good etag.
The timestamp with a microsecond resolution is a good Etag. The current ETag behaviour
is probably a good candidate to become formally part of the owncloud sync protocol.


Metadata propagation: this is currently not implemented and not specified. But for example
the ETAG of a directory should be updated whenever one of the file entries change or a
metadata of the directory changes (for example if a shared directory becomes read-only
or read-write for a user). This will allow the client to take better decisions on the
if and how to propagate the changes and report errors to users. The metadata handling
should be specified for the owncloud sync protocol.

### Case Clashes

On platforms with case preserving instead of case sensitive file systems (MacOSX and Windows)
case clashes are handled by a client side check: If a file is to be downloaded by the client
and another file that would cause a file name clash already exists, the client does not finalize 
the download but generates a user error. This should motivate the user to manually resolve 
the name clash. 

If the file name clash is resolved, the client resumes the existing hidden downloaded file.
