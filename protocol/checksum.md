# Owncloud protocol extension: checksumming

## Scope and purpose

Add checksum capability to verify end-to-end integrity of file uploads and downloads operations. 

NOT in scope: using checksums as ETAG

## Enabling transfer checksums in the client

As of version 1.7.2-cernbox and port to 1.8(.2) the type of the checksum is defined in the main config file as:
   
    [General]
    tranmissionChecksum=Adler32
   
Since client 2.2.0 checksumming is configured as server capability: https://github.com/owncloud/client/issues/4638#issuecomment-210369951   
Client discovers from the server if server supports this capability.

Checksum functionality in the client is enabled by the response to capabilities call: https://github.com/cernbox/smashbox/blob/master/protocol/protocol.md#capabilities-call

Supported checksum types are defined here: https://github.com/owncloud/client/blob/d7bd1300a8397c2782e8d75cf7c595b1ada70d88/src/libsync/propagatorjobs.h#L24

For example this response will enable Adler32 checksum on file upload and download:

      {
          "ocs": {
              "data": {
                  "capabilities": {   
                      "checksums" : {"supportedTypes" : ["Adler32"], "preferredUploadType":"Adler32"},
                      ...
                                  }
       }}}
       

## Assumptions on the checksum value

The value of Adler32 checksum MUST NOT be zero padded (2.2.4 client will complain).

## Simple PUT (not-chunked)

Client computes the checksum and sends it in the request header OC-Checksum. The OC-Checksum is defined as: checkum_type:checksum_value 

Examples:

    PUT /file HTTP/1.1
    OC-Checksum: Adler32:xxxxxxxxxxxxxxxxxx

    PUT /file HTTP/1.1
    OC-Checksum: MD5:xxxxxxxxxxxxxxxxxx


If the checksum does not match the content on the server then the server returns 412 (Precondition Failed).

    Response: 412
   
BITS NOT YET IMPLEMENTED/UNDER DISCUSSION: [see comments in the source of this file]
<!--
indicating the checksum header as the source of the error:

    Response: 412
    Response headers:
        OC-PRECONDITION-FAILED: OC-Checksum

This is to distinguish between different causes of 412 (the other common one is ETAG mismatch).
-->

## GET

Server may provide the OC-Checksum response header with the GET request. If OC-Checksum is provides then client may use it to verify the checksum on the final destination.

In case of byte-range request the OC-Checksum response header is the checksum of the entire file (like for the GET of the entire file). 

## Chunked PUT

OC-Checksum of the entire file content is sent with the last chunk PUT request (and of course should not change during the upload). 

## Remarks

The checksumming feature is optional. Client may decide NOT to provide
OC-Checksum header for PUT request and ignore OC-Checksum header
in the GET reponse. If the type of the checksum is not understood or supported by the client or by the server then
the checksum should be ignored.

Transfers should fail if the checksum type is understood and supported but the checksum value does not match.

BITS NOT YET IMPLEMENTED/UNDER DISCUSSION: [see comments in the source of this file]
<!---
For example, checksumming may be only performed by
the client if file size is smaller than OWNCLOUD_CHECKSUM_FILE_SIZE
environment variable.
-->


