from smashbox.utilities import *
from smashbox.utilities.hash_files import *


__doc__ = """
Test conflict case filenames

bug #1914: case conflict in MacOSX leading to lost files (https://github.com/owncloud/client/issues/1914)

Test input params:
  - filename : Name of the file in UpperCamelCase. For example: "TestCaseConflicts" 
  - filesizeKB:  Size of the files to be created
  - nworkers: Number of creators executed in parallel

    The function filenameVariations will generate filenames differing by case:
        For example: "TestCaseConflicts" will generate the filenames:
        ['TestCaseConflicts', 'testcaseconflicts', 'testCaseConflicts', 'testcaseConflicts', 'TestcaseConflicts', 'Testcaseconflicts', 'TestCaseconflicts', 'testCaseconflicts']

This test will generate case conflict filenames and perform the following operations:
    1) Add conflict case filenames and modify them (A simple test case)
        - It checks if there are some files lost or duplicates are generated
        - It checks if the modified files have been sync : TODO apostolos tool needs to be included in the api

    2) N clients will create files with case conflict filenames and execute the operations in 1):
        (https://github.com/owncloud/client/issues/1914#issuecomment-47698830)
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
filesizeKB = int(config.get('filenames_filesizeKB', 1000))
nworkers = int(config.get('userload_nworkers', 3))

conflict_case_list = generateConflitiveCases(filename)
conflict_cases = [item for sublist in conflict_case_list for item in sublist]
nfiles = len(conflict_cases)

""" --- Tests source code --- """


def creator(step):
    # cleanup all local files for the test
    reset_rundir()

    step(1, 'Preparation')

    d = make_workdir()
    run_ocsync(d)

    step(2, 'Add %s files with conflict case filenames ' % nfiles)

    for i in range(nfiles):
        createfile(os.path.join(d, conflict_cases[i]), '1', count=filesizeKB, bs=1000)

    logger.info("The following files has been created %s ", str(conflict_cases))

    run_ocsync(d)


@add_worker
def checker(step):
    step(3, 'Sync and check if some files are lost or duplicates')
    d = make_workdir()
    run_ocsync(d)
    N = count_files(d)

    error_check(N == (nfiles * nworkers), "Some files are lost: %d" % abs(N - (nfiles * nworkers)))

    step(4, 'Sync and check if some files are lost or duplicates are generated while it is synchronized')
    d = make_workdir()
    run_ocsync(d)

    files_1 = get_files(d)
    N = count_files(d)

    for i in range(3):
        list_files(d)
        run_ocsync(d)
        error_check(count_files(d) == N, "some files lost!")

    files_2 = get_files(d)

    for fn in set(files_1) - set(files_2):
        error_check(False, "The file has disappeared: %s" % repr(fn))

    for fn in set(files_2) - set(files_1):
        error_check(False, "New file appeared: %s" % repr(fn))

    logger.info('SUCCESS: %d files found', N)


@add_worker
def remover(step):
    step(7, 'Sync and remove half of the files')

    d = make_workdir()
    run_ocsync(d)

    for i in range(nfiles / 2):
        delete_file(os.path.join(d, conflict_cases[i]))

    step(8, 'Sync and check if the files are correctly removed')

    run_ocsync(d)
    N1 = count_files(d)

    for i in range(3):
        list_files(d)
        run_ocsync(d)
        error_check(count_files(d) == N1, "some files lost!")

    N2 = count_files(d)

    error_check(N2 == N1 / 2, 'After synch some files were not removed =%d' % (abs(N2 - N1 / 2)))

    if (N2 == N1 / 2): logger.info('SUCCESS: %d files found', N1)


reset_owncloud_account()
for i in range(nworkers):
    add_worker(creator, name="creator%02d" % (i + 1))