# Owncloud protocol extention: checksumming

## Scope and purpose

Add checksum capability to verify end-to-end integrity of file uploads and downloads operations. 

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

Client computes the checksum and sends it in the request header X-OC-Checksum. Examples:

    PUT /file HTTP/1.1
    X-OC-Checksum: "adler32:xxxxxxxxxxxxxxxxxx"

    PUT /file HTTP/1.1
    X-OC-Checksum: "md5:xxxxxxxxxxxxxxxxxx"

