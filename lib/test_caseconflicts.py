from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from protocol import file_upload
import logging
__doc__ = """
This test generates conflict case filenames (indentical names differing only by case) on the server; then the client will synchronize the files on different folders to check if the same files are downloaded on them. 
The test has been run on Windows OS (which is case insensitive) in order to reproduce a bug found on owncloud client with conflict case filenames:
 
 - Expected behaviour:
     Unix: All the files are downloaded and synchronized
     Windows: Only one file is downloaded since it is case insensitive. This file is always the same.
     
 - Actual behaviour:
     Windows: Only one file is downloaded since it is case insensitive. This file is not always the same.

Test input params:
  - filename : Name of the file in UpperCamelCase. For example: "TestCaseConflicts" 
  - filesizeKB:  Size of the files to be created
  - ndownloaders: Number of downloaders 

    The function filenameVariations will generate filenames differing by case:
        For example: "TestCaseConflicts" will generate the filenames:
        ['TestCaseConflicts', 'testcaseconflicts', 'testCaseConflicts', 'testcaseConflicts', 'TestcaseConflicts', 'Testcaseconflicts', 'TestCaseconflicts', 'testCaseconflicts']
"""

""" --- Auxiliar functions  --- """


def getPosCapLetters(filename):
    """
    Given a word; it gets the positions where are located the
    capital letters
    """
    return list(filter(lambda x: filename[x].isupper(), range(len(filename))))


def upperLowerVariations(filename, pos_list, result, i, counter):
    onecase = []
    if counter == len(pos_list) - 1:  # last case is always all lowercase
        return result
    if i == len(pos_list):  # circular list
        i = 0
    onecase = filename[0:pos_list[i]] + (filename[pos_list[i]]).lower() + filename[pos_list[i] + 1:]
    result.append(onecase)
    return upperLowerVariations(onecase, pos_list, result, i + 1, counter + 1)


def generateConflitiveCases(filename):
    """
    :return: filenames differing by case
    """
    pos_list = getPosCapLetters(filename)
    variation_list = [[filename, filename.lower()]]  ## uppercase and lowercase
    for i in range(len(pos_list)):  ## variations upper + lower
        case_list = []
        result = []
        case_list = upperLowerVariations(filename, pos_list, result, i, 0)
        variation_list.append(case_list)
    return variation_list


""" --- Test input params --- """

filename = config.get('filename', "TestCaseConflicts")

conflict_case_list = generateConflitiveCases(filename)
conflict_cases = [item for sublist in conflict_case_list for item in sublist]
nfiles = len(conflict_cases)

filesizeKB = int(config.get('filenames_filesizeKB', 10))
ndownloaders =  int(config.get('ndownloaders', nfiles))

logger =  logging.getLogger()
URL = oc_webdav_url()

""" --- Tests source code --- """

@add_worker
def creator(step):
    shared = reflection.getSharedObject()
    # cleanup all local files for the test
    reset_rundir()

    step(1, 'Preparation')

    d = make_workdir()
    run_ocsync(d)

    step(2, 'Add %s files with conflict case filenames on the server' % nfiles)

    # Windows does not allow to create multiple files differing by case. For this reason,
    # first the file is created, uploaded and then removed to be able to upload
    # from windows also files differing by case.
    for i in range(nfiles):
        filename_path = os.path.join(d, conflict_cases[i])
        create_hashfile(d, conflict_cases[i])
        file(os.path.join(d,conflict_cases[i]),'w').write(conflict_cases[i]) # it writes the name of the file on it
        file_upload(filename_path, URL)
        remove_file(filename_path)

    logger.info("The following files has been created %s ", str(conflict_cases))

    step(3, 'Sync and check if some files are lost or duplicates')
    d = make_workdir()
    run_ocsync(d)
    N = count_files(d)

    files = get_files(d)

    logger.info("The following files has been downloaded by the creator %s ", str(files))

    if(N!=nfiles):
        lost_files = list(filter(lambda x: x not in files, conflict_cases))
        error_check(len(lost_files)==0,"There are %d files lost. The filenames are %s " % (len(lost_files),str(lost_files)))
        extra_files = list(filter(lambda x: x not in conflict_cases and x not in lost_files,files))
        error_check(len(extra_files)==0,"There are %d extra files. The filenames are %s"  % (len(extra_files),str(extra_files)))

    shared['filenames_creator'] = files
    shared['creator_d'] = d



@add_worker
def downloader(step):
    shared = reflection.getSharedObject()

    step(4, 'Sync and check if the same files are downloaded in a different directory')

    d = make_workdir()
    run_ocsync(d)
    down_sync_files = get_files(d)
    logger.info("The files %s has been downloaded", str(down_sync_files))
    creator_sync_files=shared['filenames_creator']
    equal_files = list(filter(lambda x: not x[0]=="." and x not in creator_sync_files,down_sync_files))
    error_check(len(equal_files)==0,"The files %s are now downloaded and previously not" % str(equal_files))



for i in range(ndownloaders):
    add_worker(downloader,name="downloader%02d"%(i+1))