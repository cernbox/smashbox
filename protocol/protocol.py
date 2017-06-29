from smashbox.utilities import *
from smashbox.utilities.hash_files import *

import smashbox.curl

import sys,os,os.path,random

# Enable the checksuming functionality test as described in checksum.md
# The type may be: Adler32 or MD5
CHECKSUM_ENABLED=None

def enable_checksum(cstype):
    global CHECKSUM_ENABLED
    #assert(cstype in known_checksum_types)
    CHECKSUM_ENABLED=cstype

def compute_checksum(fn):
    if CHECKSUM_ENABLED:
        if CHECKSUM_ENABLED == "Adler32":
            return "Adler32:"+adler32(fn)
        if CHECKSUM_ENABLED == 'MD5':
            return "MD5:"+md5sum(fn)
    return None
        
known_checksum_types = ['MD5','Adler32']

def chunk_file_upload(filename,dest_dir_url,chunk_size=None,header_if_match=None,android_client_bug_900=False,checksum=None):
    """ Use the checksum if provided, if not calculate automatically.
    """
    
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

    if CHECKSUM_ENABLED:
        if checksum is None:
            headers['OC-Checksum'] = compute_checksum(filename)
        else:
            headers['OC-Checksum'] = checksum

    client = smashbox.curl.Client()

    for i in range(chunk_number):

        # NOTE: oc server implementation requires that chunk numbers are not zero-padded (sigh!)
        chunked_fn = "%s-chunking-%s-%s-%s"%(os.path.basename(filename),transfer_id,chunk_number,i)

        if i == chunk_number-1: # last chunk
            size = 0 # to the end of file
        else:
            size = chunk_size

        r = client.PUT(filename,os.path.join(dest_dir_url,chunked_fn),headers,offset=chunk_size*i,size=size)

        # allow for testing failures
        if header_if_match and r.rc == 412: # allow precondition failed
            return r

        if checksum is not None and r.rc == 412: # allow precondition failed if checksum was provided
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

def file_upload(filename,dest_dir_url,header_if_match=None,checksum=None):

    logger.info('file_upload: %s %s %s',filename,dest_dir_url,header_if_match)
    
    mtime = int(os.path.getmtime(filename))
    total_size = os.path.getsize(filename)

    if total_size>OWNCLOUD_CHUNK_SIZE(1):
        logger.info("File %s (%d bytes) above chunking level file too big, should be uploaded in chunks"%(filename,total_size))

    client = smashbox.curl.Client()

    headers = {'X-OC-Mtime':mtime, 'OC-Total-Length':total_size} #NOTE: OC-Total-Length seems to be ignored by the oc7 server but is still included by the client (1.6)

    if header_if_match:
        headers['If-Match'] = header_if_match

    if CHECKSUM_ENABLED:
        if checksum is None:
            headers['OC-Checksum'] = compute_checksum(filename)
        else:
            headers['OC-Checksum'] = checksum

    r = client.PUT(filename,dest_dir_url+"/"+os.path.basename(filename),headers)

    if header_if_match and r.rc == 412: # allow precondition failed
        return r

    if checksum is not None and r.rc == 412: # allow precondition failed if checksum was provided
        return r

    fatal_check(r.rc in [200,201,204]) # NOTE: 201 for new files, 204 for existing files, 200 is returned by EOS
    fatal_check('ETag' in r.headers)
    fatal_check('X-OC-Mtime' in r.headers)
    fatal_check(r.headers.get('X-OC-Mtime','').strip()=='accepted')
    fatal_check('OC-FileId' in r.headers)  

    return r


def file_download(filename,src_dir_url,dest_dir):
    import tempfile

    src_url = os.path.join(src_dir_url,filename)
    tmp_fn = tempfile.mktemp(suffix='.tmp',prefix=filename,dir=dest_dir)
    dest_fn = os.path.join(dest_dir,filename)

    client = smashbox.curl.Client()

    r = client.GET(src_url,tmp_fn)

    if r.rc == 200:
        os.rename(tmp_fn,dest_fn)
    else:
        os.unlink(tmp_fn)

    # make sure etag is present and quoted

    return r


def quota_check(url,depth=0):
    query="""<?xml version="1.0" ?>
  <d:propfind xmlns:d="DAV:"><d:prop>
      <d:quota-available-bytes/>   
      <d:quota-used-bytes/>  
  </d:prop></d:propfind>
"""

    client = smashbox.curl.Client()

    return client.PROPFIND(url,query,depth=depth)

def stat_top_level(url,depth=0):

    query="""<?xml version="1.0" ?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:getetag/>
  </d:prop>
</d:propfind>
"""

    client = smashbox.curl.Client()

    #  TODO: check if etag is quoted
    r = client.PROPFIND(url,query,depth=depth)

    for x in r.propfind_response:
        print x
    return r
   
def all_prop_android(url,depth=0):
    """ All prop request as issued by Owncloud Android Client
    """
    query="""<?xml version="1.0" encoding="UTF-8"?><D:propfind xmlns:D="DAV:"><D:allprop/></D:propfind>"""
    client = smashbox.curl.Client()

    # make sure etag is quoted
    # make sure collection type has no spaces
    # which properites to expect? compare with sabre-dav implementation
    return client.PROPFIND(url,query,depth=depth)


def ls_prop_ios_f1e09c(url,depth):
    # fixed wrong propfind (our version has allprop)
    # code ref:
    # https://github.com/owncloud/ios-library/blame/c9897927fbe5f4695369412d9f2709b352a28f59/OCCommunicationLib/OCCommunicationLib/OCWebDavClient/OCWebDAVClient.m#L274

    query="""<?xml version=\"1.0\" encoding=\"UTF-8\"?><D:propfind xmlns:D=\"DAV:\"><D:prop><D:resourcetype/><D:getlastmodified/><size xmlns=\"http://owncloud.org/ns\"/><D:creationdate/><id xmlns=\"http://owncloud.org/ns\"/><D:getcontentlength/><D:displayname/><D:quota-available-bytes/><D:getetag/><permissions xmlns=\"http://owncloud.org/ns\"/><D:quota-used-bytes/><D:getcontenttype/></D:prop></D:propfind>"""

    client = smashbox.curl.Client()

    return client.PROPFIND(url,query,depth=depth)


def ls_prop_desktop17(url,depth=0):
    """ List directory: desktop sync client 1.7
    """

    query="""<?xml version="1.0" encoding="utf-8"?>
<propfind xmlns="DAV:"><prop>
<getlastmodified xmlns="DAV:"/>
<getcontentlength xmlns="DAV:"/>
<resourcetype xmlns="DAV:"/>
<getetag xmlns="DAV:"/>
<id xmlns="http://owncloud.org/ns"/>
</prop></propfind>"""

    client = smashbox.curl.Client()

    # make sure etag is quoted

    r=client.PROPFIND(url,query,depth=depth)

    for x in r.propfind_response:
        print x
    return r


def ls_prop_desktop20(url,depth=0):
    """ List directory: desktop sync client 2.0
    """

    query= """<?xml version="1.0" encoding="utf-8"?>
<propfind xmlns="DAV:"><prop>
<getlastmodified xmlns="DAV:"/>
<getcontentlength xmlns="DAV:"/>
<resourcetype xmlns="DAV:"/>
<getetag xmlns="DAV:"/>
<id xmlns="http://owncloud.org/ns"/>
<downloadURL xmlns="http://owncloud.org/ns"/>
<dDC xmlns="http://owncloud.org/ns"/>
<size xmlns="http://owncloud.org/ns"/>
<permissions xmlns="http://owncloud.org/ns"/>
</prop></propfind>
"""

    client = smashbox.curl.Client()

    # make sure etag is quoted

    r=client.PROPFIND(url,query,depth=depth)

    fatal_check(os.path.commonprefix([x[0] for x in r.propfind_response])) # all hrefs should share a common prefix 

    for x in r.propfind_response:
        props = x[1]
        error_check(set(props.keys()) <= set(['HTTP/1.1 200 OK','HTTP/1.1 404 Not Found'])) # warn if there are other return codes for some properties

        props200 = x[1]['HTTP/1.1 200 OK']
        props404 = x[1]['HTTP/1.1 404 Not Found']

        fatal_check(props200['{DAV:}resourcetype'] in [None,'{DAV:}collection'])

        is_collection = props200['{DAV:}resourcetype'] and props200['{DAV:}resourcetype'] == '{DAV:}collection'
        fatal_check(implies(is_collection,props404['{DAV:}getcontentlength'] is None))

        fatal_check(set(props200['{http://owncloud.org/ns}permissions']) <= set('SRMWCKDNV'))

        try:
            int(props200['{http://owncloud.org/ns}size'])
        except ValueError,x:
            fatal_check(False,"{http://owncloud.org/ns}size: '%s' not an integer"%props200['{http://owncloud.org/ns}size'])
               

    return r
   

def get_url_path(url):
    """ Return the path part of the url by stripping a properly formed URL (with protocol:// prefix)
    """
    url = url[url.find('//')+2:]
    i = url.find('/')
    if i == -1: return ""
    else:
        return url[i+1:]


def create_directory(url,d):
    client = smashbox.curl.Client()
    r = client.MKCOL(os.path.join(url,d))

    fatal_check('OC-FileId' in r.headers)
    fatal_check(r.rc in [200,201,204])
    return r


def move(url,x,y):
    client = smashbox.curl.Client()

    src_url = os.path.join(url,os.path.basename(x))
    dest = get_url_path(os.path.join(url,y,os.path.basename(x)))

    r = client.MOVE(src_url,dest)
    fatal_check(r.rc in [200,201,204])
    return r


# TODO: another important test: 409 is required if trying to upload to non-existing directory

