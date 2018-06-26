from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import *

"""
Observations:

eos attr set sys.tmp.etag= -- changes mtime (and DAV:getlastmodified) of the file, no effect on the directory, this is NOT a regression (same behaviour on eosuser)

NOTE: I need to handle ETAG quotes in my script (set_tmp_etags.sh)!


"""

@add_worker
def main(step):

    d = make_workdir()

    URL = oc_webdav_url()


    propfind = ls_prop_desktop20
    #propfind = all_prop_android

    BASEURL=URL.replace('/cernbox/desktop/remote.php/webdav/home','')

    def scan_dir(URL):
        r0=propfind(URL,depth=0).propfind_response
        r1=propfind(URL,depth=1).propfind_response

        # the parent dir (.) reported by Depth1 must be identical as the parent dir reported by Depth0
        r10=[x for x in r1 if x[0] == r0[0][0]]
        assert r0 == r10

        print r0[0][0],r0[0][1]['HTTP/1.1 200 OK']

        for x in r1:
            if x[0] == r0[0][0]:
                continue
            path=x[0]
            attrs=x[1]['HTTP/1.1 200 OK']

            if attrs['{DAV:}resourcetype'] == '{DAV:}collection':
                # recurse into the directory
                scan_dir(BASEURL+path)
            else:
                print path,attrs


    scan_dir(URL)
