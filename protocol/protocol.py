from smashbox.utilities import *
from smashbox.utilities.hash_files import *

import smashbox.curl

import sys,os,os.path,random

def chunk_file_upload(filename,dest_dir_url,chunk_size=None,header_if_match=None,android_client_bug_900=False):


    logger.info('chunk_file_upload: %s %s %s %s %s',filename,dest_dir_url,chunk_size,header_if_match,android_client_bug_900)

    if chunk_size is None:
        chunk_size = OWNCLOUD_CHUNK_SIZE(1)

    mtime = int(os.path.getmtime(filename))

    # calculate chunk number
    total_size = os.path.getsize(filename)
    chunk_number = total_size/chunk_size

    if chunk_number==0:
        logger.info('chunk_file_upload: File %s too small (%d bytes) and should be uploaded unchunked',filename,total_size)

    if total_size % chunk_size: # add reminder if exists
        chunk_number += 1

    # NOTE: 1.6 mirall implementation: rand() ^ mtime ^ (size << 16), propagator_qnam.cpp
    transfer_id = random.randint(0,sys.maxint)

    headers = {'OC-Chunked':'1', 'X-OC-Mtime':mtime, 'OC-Total-Length':total_size}

    if android_client_bug_900: # emulate this bug: https://github.com/owncloud/android/issues/900
        del headers['OC-Total-Length']

    if header_if_match:
        headers['If-Match'] = header_if_match

    client = smashbox.curl.Client()

    for i in range(chunk_number):

        # NOTE: oc server implementation requires that chunk numbers are not zero-padded (sigh!)
        chunked_fn = "%s-chunking-%s-%s-%s"%(os.path.basename(filename),transfer_id,chunk_number,i)

        if i == chunk_number-1: # last chunk
            size = 0 # to the end of file
        else:
            size = chunk_size

        r = client.PUT(filename,os.path.join(dest_dir_url,chunked_fn),headers,offset=chunk_size*i,size=size)

        if header_if_match and r.rc == 412: # allow precondition failed
            return r

        oc_rc_codes = [201] # NOTE: always 201, no difference if first or last chunk
        eos_rc_codes = [200]

        fatal_check(r.rc in oc_rc_codes+eos_rc_codes, "rc=%s"%r.rc)

        if i < chunk_number-1: # not last chunk

            # NOTE: this is critical, otherwise client is confused
            fatal_check('ETag' not in r.headers)
            fatal_check('X-OC-Mtime' not in r.headers)

            # NOTE: if file previously existed OC-FileId is returned here (oc7 server)
            # NOTE: so client (in theory at least) should not depend on this and hence this should not be part of the protocol
            #fatal_check('OC-FileId' in reply_headers)  

        else: # last chunk
            fatal_check('ETag' in r.headers)
            fatal_check('X-OC-Mtime' in r.headers)
            fatal_check(r.headers.get('X-OC-Mtime','').strip()=='accepted')
            fatal_check('OC-FileId' in r.headers)  

    return r

def file_upload(filename,dest_dir_url,header_if_match=None):

    logger.info('file_upload: %s %s %s',filename,dest_dir_url,header_if_match)
    
    mtime = int(os.path.getmtime(filename))
    total_size = os.path.getsize(filename)

    if total_size>OWNCLOUD_CHUNK_SIZE(1):
        logger.info("File %s (%d bytes) above chunking level file too big, should be uploaded in chunks"%(filename,total_size))

    client = smashbox.curl.Client()

    headers = {'X-OC-Mtime':mtime, 'OC-Total-Length':total_size} #NOTE: OC-Total-Length seems to be ignored by the oc7 server but is still included by the client (1.6)

    if header_if_match:
        headers['If-Match'] = header_if_match

    r = client.PUT(filename,os.path.join(dest_dir_url,os.path.basename(filename)),headers)

    if header_if_match and r.rc == 412: # allow precondition failed
        return r

    fatal_check(r.rc in [200,201,204]) # NOTE: 201 for new files, 204 for existing files, 200 is returned by EOS
    fatal_check('ETag' in r.headers)
    fatal_check('X-OC-Mtime' in r.headers)
    fatal_check(r.headers.get('X-OC-Mtime','').strip()=='accepted')
    fatal_check('OC-FileId' in r.headers)  

    return r

def file_download(filename,src_dir_url,dest_dir):
    
    src_url = os.path.join(src_dir_url,filename)
    dest_fn = os.path.join(dest_dir,filename)

    client = smashbox.curl.Client()

    r = client.GET(src_url,dest_fn)

    return r


# TODO: another important test: 409 is required if trying to upload to non-existing directory

