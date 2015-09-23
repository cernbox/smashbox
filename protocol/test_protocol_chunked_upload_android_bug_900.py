from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import chunk_file_upload,file_upload, file_download

@add_worker
def main(step):

    d = make_workdir()
    reset_owncloud_account()

    # we make client look like an Android client
    config.pycurl_USERAGENT = "Android-ownCloud"

    # this test should be run against the mobile endpoint of cernbox which may be convinently set in the config
    # for vanilla owncloud server mobile endpoint is the same as generic webdav endpoint
    webdav_endpoint = config.get('oc_mobile_webdav_endpoint',None)

    URL = oc_webdav_url(webdav_endpoint=webdav_endpoint)

    if webdav_endpoint is None:
        logger.warning('oc_mobile_webdav_endpoint was not defined, using standard endpoint, URL: %s',URL)

    # chunk size defined in the android source code
    # https://github.com/owncloud/android-library/blob/d7097983594347167b5bde3fa5b2b4ad1d843392/src/com/owncloud/android/lib/resources/files/ChunkedUploadRemoteFileOperation.java#L45
    # Note: specifying a different chunk size will result in corrupted file!
    # This is a hack until the android-client is properly fixed!

    ANDROID_CHUNKSIZE=1024*1000 

    filename=create_hashfile(d,size=int(5.5*ANDROID_CHUNKSIZE))

    # careful with the chunk size...
    r=chunk_file_upload(filename,URL,chunk_size=ANDROID_CHUNKSIZE,android_client_bug_900=True)
    file_download(os.path.basename(filename),URL,d)
    analyse_hashfiles(d)

    # upload again matching the existing etag
    r=chunk_file_upload(filename,URL,chunk_size=ANDROID_CHUNKSIZE,android_client_bug_900=True,header_if_match=r.headers['ETag'])
    analyse_hashfiles(d)

    # upload again with a non-matching etag
    r = chunk_file_upload(filename,URL,header_if_match='!@# does not exist 123')
    fatal_check(r.rc == 412) # precondition failed

    # TODO: 
    #  - make sure that without user agent header the upload fails
    #  - 
