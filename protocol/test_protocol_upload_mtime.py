from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import chunk_file_upload, file_upload, ls_prop_desktop20, ls_prop_desktop17, all_prop_android

import time
import dateutil.parser

def check_propfind_response(URL,filename,mtime,total_size):

    filename = os.path.basename(filename)

    for propfind in [ls_prop_desktop20,ls_prop_desktop17, all_prop_android]:

        r0=propfind(URL,depth=1).propfind_response
        #r1=propfind(URL+"/"+filename,depth=0).propfind_response #FIXME: PROPFIND of individual file does not work?

        resp = [x for x in r0 if x[0] == '/cernbox/desktop/remote.php/webdav/home/'+filename][0]

        r=resp[1]['HTTP/1.1 200 OK']

        assert(int(r['{DAV:}getcontentlength']) == total_size)

        # convert GMT mtime reported by PROPFIND to EPOCH
        d1=dateutil.parser.parse(r['{DAV:}getlastmodified'])-datetime.datetime(1970,1,1,tzinfo=dateutil.tz.tzutc())
        d1=d1.days*86400+d1.seconds

        d2=int(mtime)

        if d1 != d2:
            print resp
            print filename
            print d1,d2
            assert("MTIME DOES NOT MATCH" is False)




@add_worker
def main(step):

    d = make_workdir()
    reset_owncloud_account()

    URL = oc_webdav_url()

    filename=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(0.3))
    time.sleep(2)
    mtime = int(os.path.getmtime(filename))
    total_size = os.path.getsize(filename)
    r=file_upload(filename,URL)

    check_propfind_response(URL,filename,mtime,total_size)

    filename=create_hashfile(d,size=OWNCLOUD_CHUNK_SIZE(3.3))
    time.sleep(2)
    mtime = int(os.path.getmtime(filename))
    total_size = os.path.getsize(filename)
    r=chunk_file_upload(filename,URL)

    check_propfind_response(URL,filename,mtime,total_size)


