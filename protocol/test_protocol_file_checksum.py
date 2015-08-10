from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import chunk_file_upload, file_upload, file_download
import smashbox.protocol

import os
import os.path

@add_worker
def main(step):

    d = make_workdir()
    reset_owncloud_account()

    URL = oc_webdav_url()

    logger.info('*** 0. upload without the checksum (files should be accepted by the server)')

    filename1=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(0.1))
    filename2=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(3.3))

    # upload the file without a checksum and then download it to get the checksum type used by the server
    file_upload(filename1,URL)
    chunk_file_upload(filename2,URL)

    file_download(os.path.basename(filename1),URL,d)
    r=file_download(os.path.basename(filename2),URL,d)

    analyse_hashfiles(d) # make sure that files uploaded without a checksum are not corrupted

    logger.info('Got checksum from the server: %s', r.headers['OC-CHECKSUM'])

    try:
        active_server_checksum_type = r.headers['OC-CHECKSUM'].strip().split(':')[0]
    except KeyError,x:
        logger.warning('Checksum not enabled for %s',oc_webdav_url(hide_password=True))
        return

    # now check the checksum type supported on the server
    logger.info('Server supports %s checksum',repr(active_server_checksum_type))
    smashbox.protocol.enable_checksum(active_server_checksum_type)

    logger.info('*** 1. upload with correct checksum (files should be accepted by the server)')

    filename1=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(0.1))
    filename2=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(3.3))

    file_upload(filename1,URL)
    chunk_file_upload(filename2,URL)

    file_download(os.path.basename(filename1),URL,d)
    file_download(os.path.basename(filename2),URL,d)

    analyse_hashfiles(d)   

    # pass around  incorrect checksum (of the type supported by the server)
    # the puts should be failing

    def corrupted_checksum(fn):
        c = smashbox.protocol.compute_checksum(fn)
        c = c[:-1]+chr(ord(c[-1])+1)
        return c

    logger.info('*** 2. upload with corrupted checksum value (files should be refused by the server)')

    filename1=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(0.1))
    filename2=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(3.3))        

    r = file_upload(filename1,URL,checksum=corrupted_checksum(filename1))
    fatal_check(r.rc == 412)

    r = chunk_file_upload(filename2,URL,checksum=corrupted_checksum(filename2))
    fatal_check(r.rc == 412)

    # paranoia check: make sure that the server did not store the corrupted files inspite of returning 412

    d_corrupted = mkdir(os.path.join(d,'corrupted_files'))
    file_download(os.path.basename(filename1),URL,d_corrupted)
    file_download(os.path.basename(filename2),URL,d_corrupted)

    fatal_check(os.listdir(d_corrupted)==[])

    # pass around a checksum of the type unsupported by the server, including some garbage types (which are not even well-formatted)
    # in this case the checksums should be ignored and the files transmitted as if checksum was not provided at all
    checksum_types = list(set(smashbox.protocol.known_checksum_types)-set([active_server_checksum_type]))

    checksum_types += ['blabla']

    logger.info('*** 3. upload with corrupted checksum types and strange values (files should be accepted by the server)')

    for value in ['',':bah',':']:
        for cstype in checksum_types:

            smashbox.protocol.enable_checksum(cstype)

            filename1=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(0.1))
            filename2=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(3.3))        

            logger.info(' *** testing checkum value: '+cstype+value)
            
            file_upload(filename1,URL,checksum=cstype+value)
            chunk_file_upload(filename2,URL,checksum=cstype+value)

            file_download(os.path.basename(filename1),URL,d)
            file_download(os.path.basename(filename2),URL,d)

            analyse_hashfiles(d)               
