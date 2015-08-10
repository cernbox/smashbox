from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import file_upload, file_download

@add_worker
def main(step):

    d = make_workdir()
    reset_owncloud_account()

    URL = oc_webdav_url()

    filename=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(0.3))

    r=file_upload(filename,URL)
    file_download(os.path.basename(filename),URL,d)
    analyse_hashfiles(d)

    # upload again matching the existing etag
    r=file_upload(filename,URL,header_if_match=r.headers['ETAG'])
    analyse_hashfiles(d)

    # upload again with a non-matching etag
    r = file_upload(filename,URL,header_if_match='!@# does not exist 123')
    fatal_check(r.rc == 412) # precondition failed

    # upload file to a directory which does not exist on the server
    import uuid
    r = file_upload(filename,os.path.join(URL,str(uuid.uuid1())), allow_failure=True)
    fatal_check(r.rc == 409,'server replied: %s'%r.rc) # expected 409 Conflict according to http://www.webdav.org/specs/rfc4918.html#METHOD_PUT
