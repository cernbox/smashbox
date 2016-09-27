File chunking (new generation)
====

This is a work in progress (July 2016) to introduce a better chunking protocol than currently implemented 
(which has many drawbacks such server keeping the tranfser state implicitly which results poor error recovery possibilities).

The specification will be added gradually here.


References
==========

Initial ideas and discussion:

 * https://dragotin.wordpress.com/2015/06/22/owncloud-chunking-ng/
 * https://dragotin.wordpress.com/2015/07/10/owncloud-chunking-ng-part-2-announcing-an-upload/
 * https://dragotin.wordpress.com/2015/11/13/owncloud-chunking-ng-part-3-incremental-syncing/
 
Overview
========

If the file size exceeds a certain size, the file is split into chunks.
The client generates an unique transfer id.

1. The client generates an unique transfer id, and creates a directory in the upload
path with the transferId.

2. The client can then upload chunks in whatever order in that directory
using the PUT method. The name of every chunk should be its chunk number.

3. Once all the chunks have been uploaded, the client can issue a MOVE
to finalize the upload.


MKCOL
=====

First, the client generates a transfer id and creates a directory for uploading the chunks

   MKCOL /remote.php/dav/uploads/<user-id>/<transfer-id>

The MKCOL SHOULD have a `OC-Total-Length` header which is the final size of the file

The server should reply with 201 Created.

PUT
===

The client can upload the chunks in any order or in parallel, chunks size can vary
during upload. Chunk should be ordered, and the name is the chunk number

   PUT /remote.php/dav/uploads/<user-id>/<transfer-id>/<chunk-number>

The client sends an additional header with every chunk: `OC-Chunk-Offset` is the
starting position of the chunk in the final files, in bytes.

MOVE
====

When all the chunk have been uploaded, the client can issue a MOVE of a special
`.file` to the final destination of the file

  MOVE /remote.php/dav/uploads/<user-id>/<transfer-id>/.file
  Destination: /remote.php/dav/files/<user-id>/path/to/file.dat

Additional headers:

* `X-OC-Mtime`: has the same meaning than for a normal file upload
* `If-Destination-Match`: Has the same meaning than an `If-Match` in a normal upload.
* `OC-Checksum`: The checksum of the full file, see checksum.md

The server replies with code 201 when the file was created or 204 if it was updated.

Response Custom Header:

`OC-Etag` - Same meaning as in normal file upload.
`OC-FileId` - Same meaning as in normal file upload.

PROPFIND
========

The client may do a PROPFIND on the directory. The server will return a list
of every uploaded chunks and their size. So the client will know how to continue.

