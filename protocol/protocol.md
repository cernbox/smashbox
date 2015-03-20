# OC Sync Protocol

Document Author: Jakub.Moscicki@cern.ch

Document Date: 2014-08-21

This document is part of cernbox project (AGPL license).

## Introduction

This is an attempt to describe the protocol used by owncloud desktop client for syncing files.

Applies to owncloud client 1.6 and owncloud server 6 and 7. We are deliberately omitting older implementation which require obsolete methods (such as PROPPATCH to set mtime after PUT).

Owncloud desktop client uses a mix of HTTP REST calls and WEBDAV with few header extentions and conventions.

Minimalistic doc style. Work in progress.

## Authorization

Currently the only method supported (in the scope of this version of this document) is basic authorization.

Unless it is specified explicitly all calls must be authorised (https or http with authorization header).

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

TODO: also range requests


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

Response example for owncloud 7.0.1 community edition:

    {"installed":"true","version":"7.0.1.1","versionstring":"7.0.1","edition":""}



## WEBDAV

Standard webdav request/response conventions apply. 

Namespace for non-standard properties: `http://owncloud.org/ns`

### Restrictions and limitations

#### Properties

The etag value must be "quoted". 

In the response body the value of resourcetype property MUST NOT contain whitespaces (implementation as of owncloud client 1.5):   
   
        <d:resourcetype><d:collection/></d:resourcetype>

#### Headers

PROPFIND Depth:infinity is not supported: client will try this for compatibility with older code  but server may choose to return 501 (not implemented).



### Quota check

Syntax:
	    
	PROPFIND /remote.php/webdav/ HTTP/1.1
	Depth: 0
	
	<?xml version="1.0" ?>
	  <d:propfind xmlns:d="DAV:"><d:prop>
	      <d:quota-available-bytes/>   
	      <d:quota-used-bytes/>  
	  </d:prop></d:propfind>

Response: 207

Reponse body example:

    <?xml version="1.0" encoding="utf-8"?>
     <d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns">
      <d:response>
        <d:href>/remote.php/webdav/</d:href>
        <d:propstat>
          <d:prop>
            <d:quota-available-bytes>107347967021</d:quota-available-bytes>
            <d:quota-used-bytes>26215379</d:quota-used-bytes>
          </d:prop>
          <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
      </d:response>
     </d:multistatus>

### Stat top-level directory

Syntax:

    PROPFIND /remote.php/webdav/ HTTP/1.1
    Depth: 0

    <?xml version="1.0"?>
     <d:propfind xmlns:d="DAV:"><d:prop>
       <d:getlastmodified />
     </d:prop></d:propfind>    
    
Reponse: 207

Response body example:

	<?xml version="1.0" encoding="utf-8"?>
	<d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns">
	  <d:response>
	    <d:href>/remote.php/webdav/</d:href>
	    <d:propstat>
	      <d:prop>
	        <d:getlastmodified>Wed, 30 Apr 2014 08:50:03 GMT</d:getlastmodified>
	      </d:prop>
	      <d:status>HTTP/1.1 200 OK</d:status>
	    </d:propstat>
	  </d:response>
	</d:multistatus> 
	 
    

Comment: 

- seen issued to the top level directory only

### List directory

List directory _path_ and return mtime, size, type, etag and file id.

Syntax:

    PROPFIND /remote.php/webdav/path HTTP/1.1
    Depth: 1
    
    <?xml version="1.0" encoding="utf-8"?>
	 <propfind xmlns="DAV:"><prop>
	  <getlastmodified xmlns="DAV:"/>
	  <getcontentlength xmlns="DAV:"/>
	  <resourcetype xmlns="DAV:"/>
	  <getetag xmlns="DAV:"/>
	  <id xmlns="http://owncloud.org/ns"/>
	</prop></propfind>

Non-standard property: id (FileId)

Response: 207

Response body: see restrictions and limitations paragraph

Response body example:

    PROPFIND /remote.php/webdav/New%20folder HTTP/1.1
    
    <?xml version="1.0" encoding="utf-8"?>
	<d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns" xmlns:oc="http://owncloud.org/ns">
	  <d:response>
	    <d:href>/remote.php/webdav/New%20folder/</d:href>
	    <d:propstat>
	      <d:prop>
	        <oc:id>00000287ocee55caa1e4</oc:id>
	        <d:getetag>"5391c8e1e4cf0"</d:getetag>
	        <d:getlastmodified>Fri, 06 Jun 2014 13:57:53 GMT</d:getlastmodified>
	        <d:resourcetype><d:collection/></d:resourcetype>
	      </d:prop>
	      <d:status>HTTP/1.1 200 OK</d:status>
	    </d:propstat>
	    <d:propstat>
	      <d:prop>
	        <d:getcontentlength/>
	      </d:prop>
	      <d:status>HTTP/1.1 404 Not Found</d:status>
	    </d:propstat>
	  </d:response>
	  <d:response>
	    <d:href>/remote.php/webdav/New%20folder/file.txt</d:href>
	    <d:propstat>
	      <d:prop>
	        <oc:id>00000292ocee55caa1e4</oc:id>
	        <d:getetag>"5391c8e19e24f"</d:getetag>
	        <d:getlastmodified>Fri, 06 Jun 2014 13:57:53 GMT</d:getlastmodified>
	        <d:getcontentlength>55</d:getcontentlength>
	        <d:resourcetype/>
	      </d:prop>
	      <d:status>HTTP/1.1 200 OK</d:status>
	    </d:propstat>
	  </d:response>
	</d:multistatus>  


### Create directory

### Move file or directory

### Remove file or directory

    
## HTTP

### Download file
### Upload file
### Upload files (chunked)

## Upcoming changes

Custom header: OC-Etag 

See:
 - https://github.com/owncloud/client/issues/1291#issuecomment-77165925)
 - https://github.com/owncloud/client/search?utf8=%E2%9C%93&q=oc-etag



# OC Sync semantics


## Lifecycle and semantics of FileId vs path vs etag 

The FileId is suitable for tracking the server-side moves but it is not suitable for making permanent one-to-one associations of remote and local paths for purposes such as avoiding case clashes with case-insensitive clients.

This is because the FileId associated with a path may change in time. For example, if you delete a file/directory on the server and then recreate it with the same name -- it will get a new FileId. So FileId really acts as an inode number and it should be assumed that it may change for the same path at any time. Implementation of another behaviour (be it in the database or directly on storage) is impractical. So current behaviour is probably a good candidate to become formally part of the owncloud sync protocol.

Although the same path may have different values of FileId over the course of its lifetime, it is guaranteed that FileIds never repeat. The remote move detection is thus based on the fact that the set of server changes (as detected by the client) contains a new path which is associated with a previously known FileId. The client remembers the old path associated with the FileId and thus may propagate the remote move by performing a local move from old path to new. It is up to the client to track local moves, so it should be able to propagate the remote move correctly even if the same local path was also moved at the same time.

The sync protocol concerns keeping *paths* consistent between the clients and the server: when a change is detected then it is propagated to the corresponding path on the other side. 
Detection of local path modifications is up to the client. Etag is used by the clients to understand if a path has changed on the server. When a path is changed on the server it's Etag will get a new, unique value. Etag must have a property such that if there is a change of content of a path, it is guaranteed that the new value of the Etag will not be equal to any previous Etag values that a client may have seen in the past. Otherwise changes could remain undetected if paths were renamed or moved. UUID is a good Etag because it is unique across the entire namespace. An integer per file version number (0,1,2,…) which is incremented on every update of that file if not a good Etag.  A strong checksum on file content is the most efficient Etag because it allows to ignore the updates which do not change the content. For directories: the UUID is a good etag. The timestamp with a microsecond resolution is a good Etag. The current ETag behaviour is probably a good candidate to become formally part of the owncloud sync protocol.

Metadata propagation: this is currently not implemented and not specified. But for example the ETAG of a directory should be updated whenever one of the file entries change or a metadata of the directory changes (for example if a shared directory becomes read-only or read-write for a user). This will allow the client to take better decisions on the if and how to propagate the changes and report errors to users. The metadata handling should be specified for the owncloud sync protocol.


### Practical implications (version 1.6 and 6.0.3)

Case-clashes are not handled efficiently and lead to data loss but it is not even clear how correct behaviour could be achieved in the model described above:
<http://github.com/owncloud/mirall/issues/1914>

The move functionality is broken but there are not a-priori contradictions in the protocol so it should be possible to fix within the model described above:
<http://github.com/owncloud/mirall/issues/1933>

