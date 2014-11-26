# Owncloud protocol extension: checksumming

## Scope and purpose

Add checksum capability to verify end-to-end integrity of file uploads and downloads operations. First prototype implementation is adler32.

NOT is scope: using checksums as ETAG

## Enabling transfer checksums in the client

Client discovers from the server if server supports this capability.

Checksum functionality in the client is enabled by the respose to status.php:

    GET /status.php HTTP/1.1

Response body examples:

    {...., "transfer_checksum":""}
    {...., "transfer_checksum":"alder32"}
    {...., "transfer_checksum":"md5"}

In the future "transfer_checksum" may be enabled on per-folder basis as a PROPFIND property on the remote folder.

## Simple PUT (not-chunked)

Client computes the checksum and sends it in the request header X-OC-Checksum. The X-OC-Checksum is defined as: checkum_type:checksum_value 

Examples:

    PUT /file HTTP/1.1
    X-OC-Checksum: adler32:xxxxxxxxxxxxxxxxxx

    PUT /file HTTP/1.1
    X-OC-Checksum: md5:xxxxxxxxxxxxxxxxxx

If the checksum does not match the content on the server then the server returns 412 (Precondition Failed) indicating the checksum header as the source of the error:

    Response: 412
    Response headers:
        X-OC-PRECONDITION-FAILED: X-OC-Checksum

This is to distinguish between different causes of 412 (the other common one is ETAG mismatch).


## GET

Server may provide the X-OC-Checksum response header with the GET request. If X-OC-Checksum is provides then client may use it to verify the checksum on the final destination.

In case of byte-range request the X-OC-Checksum response header is the checksum of the entire file (like for the GET of the entire file). 

## Chunked PUT

X-OC-Checksum of the entire file content is sent with every chunk PUT request (and of course should not change during the upload). 

## Remarks

The checksumming feature is optional. Client may decide NOT to provide
X-OC-Checksum header for PUT request and ignore X-OC_Checksum header
in the GET reponse. For example, checksumming may be only performed by
the client if file size is smaller than OWNCLOUD_CHECKSUM_FILE_SIZE
environment variable.



