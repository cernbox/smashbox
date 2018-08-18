from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import *

import smashbox.curl

"""
Observations:

eos attr set sys.tmp.etag= -- changes mtime (and DAV:getlastmodified) of the file, no effect on the directory, this is NOT a regression (same behaviour on eosuser)

NOTE: I need to handle ETAG quotes in my script (set_tmp_etags.sh)!


"""

FILTER_OUT_ATTRS=True
EOS_BUG_2732 = True
IGNORE_FOLDER_SIZE=False

@add_worker
def main(step):

    user=config.oc_account_name
    user_letter=user[0]
    server=config.oc_server
    extra_path=''

    assert(user!='.')
    assert(config.oc_server in ['eoshome','eosuser'])

    if config.oc_server == 'eoshome':
       server = 'eoshome-'+user_letter
       extra_path='/.ongoing'

    URL = 'http://'+server+':8000/cernbox/desktop/remote.php/webdav/home/'

    smashbox.curl.Client.extra_headers={'Remote-user':user, 'CBOX-CLIENT-MAPPING':'cernbox/desktop/remote.php/webdav/home', 'CBOX-SERVER-MAPPING':'eos/user%s/%s/%s'%(extra_path,user_letter,user),'X-Real-IP':'127.0.0.1'}

    propfind = ls_prop_desktop20
    #propfind = all_prop_android

    BASEURL=URL.replace('/cernbox/desktop/remote.php/webdav/home','')

    NSDAV="{DAV:}"
    NSOC="{http://owncloud.org/ns}"

    
    ids_files=[]
    ids_directories=[]
    etags_directories=[]

    fout = file('report.propfind.%s.%s.txt'%(user,config.oc_server),'w',0)

    propfind_list=[]
    
    def scan_dir(URL):
        try:
            r0=propfind(URL,depth=0).propfind_response
            r1=propfind(URL,depth=1).propfind_response
        except Exception,x:
            print >> sys.stderr, "ERROR: Failed to propfind",URL
            raise


        # the parent dir (.) reported by Depth1 must be identical as the parent dir reported by Depth0
        r10=[x for x in r1 if x[0] == r0[0][0]]
        
        if r0 != r10 and not EOS_BUG_2732:
            print "ERROR: r0 != r10"
            print "URL",URL
            print "r0",r0
            print "r10",r10
            sys.exit(-1)
        
        path=r0[0][0]
        attrs=r0[0][1]['HTTP/1.1 200 OK']

        ids_directories.append(attrs[NSOC+'id'])
        etags_directories.append(attrs[NSDAV+'getetag'])

        if FILTER_OUT_ATTRS:
            attrs[NSOC+'id'] = 'DDD' # this attribute does not matter for comparison of directories
            attrs[NSDAV+'getlastmodified'] = 'DDD' # this attribute does not matter for comparison of directories
            attrs[NSDAV+'getetag'] = 'DDD' # this attribute does not matter for comparison of directories
            if IGNORE_FOLDER_SIZE:
                attrs[NSOC+'size'] = 'DDD'

        print >> fout, repr(path),repr(attrs)

        for x in sorted(r1):
            if x[0] == r0[0][0]:
                continue
            path=x[0]
            attrs=x[1]['HTTP/1.1 200 OK']

            if attrs['{DAV:}resourcetype'] == '{DAV:}collection':
                # recurse into the directory
                scan_dir(BASEURL+path)
            else:

                ids_files.append(attrs[NSOC+'id'])
                if FILTER_OUT_ATTRS:
                    attrs[NSOC+'id'] = 'FFF' # this attribute does not matter for comparison of files
                    if EOS_BUG_2732:
                        attrs[NSDAV+'getlastmodified'] = 'FFF' # buggy mtime should not be compared

                propfind_list.append((repr(path),repr(attrs)))

                print >> fout, repr(path),repr(attrs)

    scan_dir(URL)

    fout.close()

    fout1 = file('report.f-ids.%s.%s.txt'%(user,config.oc_server),'w',0)
    for x in sorted(ids_files):
        print >> fout1, x

    fout2 = file('report.d-ids.%s.%s.txt'%(user,config.oc_server),'w',0)
    for x in sorted(ids_directories):
        print >> fout2, x

    fout3 = file('report.d-etags.%s.%s.txt'%(user,config.oc_server),'w',0)
    for x in sorted(etags_directories):
        print >> fout3, x




