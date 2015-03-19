from smashbox.utilities import * 
from smashbox.utilities.hash_files import count_files

import os

__doc__ = """ Test various characters in the file names.

bug #104648: add UTF-8 escaping in PROPFIND response body (https://savannah.cern.ch/bugs/?104648)

Notes:
 - unescaped % characters in propfind response crashes csync

"""

filesizeKB = int(config.get('filenames_filesizeKB',1))

# see: mirall/csync/src/csync_exclude.c
charsets_excluded_from_sync = {
                 'backslash' : '\\',
                 'colon' : ':',
                 'questionmark' : '?',
                 'asterisk' : '*',
                 'doublequote' : '"',
                 'greater' : '>',
                 'smaller' : '<',
                 'pipe'    : '|'
}

def is_excluded(name):
    """
    Returns true if the given file name matches an pattern
    excluded from sync by the sync client.

    :param name: file name to check
    :returns: True if the file name must be excluded, False otherwise
    """
    if name == '.': # skip this
        return True

    # excluded pattern "*~"
    if name[-1] == '~':
        return True

    # excluded pattern "._*"
    if len(name) >= 2 and name[0:2] == '._':
        return True

    file_name, ext = os.path.splitext(name)

    # excluded pattern "*.~*"
    if len(ext) > 1 and ext[1] == '~':
        return True

    return False

@add_worker
def creator(step):
    
    reset_owncloud_account()
    reset_rundir()

    step(1,'create initial content and sync')

    d = make_workdir()

    namepatterns = [
        "space1 testfile.dat",
        "space2testfile .dat",
        " space3testfile .dat",
        "space4testfile.dat ",
        "space5testfile. dat",
        " space6 testfile . dat ",
        " "
    ]

    charsets = { 'space' : ' ', 
                 'plus' : '+', 
                 'underscore' : '_',
                 'moscicki' : '\xc5\x9b', # some UTF-8 unicode character...
                 'singlequote' : "'"
        }

    charsets.update(charsets_excluded_from_sync)
    
    filenames = []

    for c in charsets:
        for n in namepatterns:
            nn =  n.replace('space', "_"+c+"_").replace(' ',charsets[c]) 
            #print nn
            filenames.append(nn)
            createfile(os.path.join(d,nn),'1',count=filesizeKB,bs=1000)

    # generic charsets -- let's take a hammer and test (almost) all ANSI characters
    # we don't test for the foward slash
    char_range = range(32,47)+range(58,65)+range(91,97)+range(123,127)

    #char_range.remove(37) #to see the tests to complition temporarily remove this character as it crashes csync
    #char_range=[]
    for i in char_range:
        for n in namepatterns:
            nn = n.replace('space','_chr'+str(i)+'_').replace(' ',chr(i))
            if nn == '.': # skip this
                continue 
            filenames.append(nn)
            createfile(os.path.join(d,nn),'1',count=filesizeKB,bs=1000)

    files_1 = os.listdir(d)
    N = count_files(d)

    shared = reflection.getSharedObject()

    shared['files_1'] = files_1
    shared['N'] = N

    for i in range(3): # 2 is enough but 3 is better ;-)
        list_files(d)
        run_ocsync(d)
        error_check(count_files(d) == N, "some files lost!")

    files_2 = os.listdir(d)

    for fn in set(files_1)-set(files_2):
        error_check(False, "the file has disappeared: %s"%repr(fn))



@add_worker
def propagator(step):

    step(2,'check propagation of files')

    d = make_workdir()

    shared = reflection.getSharedObject()

    files_1 = shared['files_1']

    # take the original file list produced by creator and remove all file names containing characters excluded from sync
    expected_files = [fn for fn in files_1 if not any((c in charsets_excluded_from_sync.values()) for c in fn) ]
    # also exclude file name patterns
    expected_files = [fn for fn in expected_files if not is_excluded(fn)]

    logger.info("expected %d files to be propagated (excluding the ones with unsyncable characters %s)",len(expected_files),repr(charsets_excluded_from_sync.values()))

    run_ocsync(d)

    N2 = count_files(d)
    files_3 = os.listdir(d)

    for fn in set(expected_files)-set(files_3):
        error_check(False, "the file has not been propagated: %s"%repr(fn))
