from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import chunk_file_upload, file_upload, file_download

@add_worker
def main(step):

    d = make_workdir()
    reset_owncloud_account()

    URL = oc_webdav_url()

    filename=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(3.3))

    r=chunk_file_upload(filename,URL)
    file_download(os.path.basename(filename),URL,d)
    analyse_hashfiles(d)

    # upload again matching the existing etag
    r=chunk_file_upload(filename,URL,header_if_match=r.headers['ETag'])
    analyse_hashfiles(d)

    # upload again with a non-matching etag
    r = chunk_file_upload(filename,URL,header_if_match='!@# does not exist 123')
    fatal_check(r.rc == 412) # precondition failed
