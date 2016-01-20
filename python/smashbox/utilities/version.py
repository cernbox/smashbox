import operator


def version_compare(v1, operator, v2):
    """
    The function first replaces _, - and + with a dot . in the version strings and also inserts dots . before and
    after any non number so that for example '4.3.2RC1' becomes '4.3.2.RC.1'. Then it compares the parts starting
    from left to right. If a part contains special version strings these are handled in the following order:
        any string not found in this list < dev < alpha = a < beta = b < RC = rc < #
    This way not only versions with different levels like '4.1' and '4.1.2' can be compared but also any version
    containing development state.

    :param v1: Version to compare
    :param operator: Can be one of <, <=, =, !=, >=, >
    :param v2: Version to compare against
    :return: Boolean
    """
    return __version_compare_tuple(__normalize_version(v1), operator, __normalize_version(v2))


def __version_compare_tuple(t1, compare, t2):

    # Make both versions the same length
    if len(t1) < len(t2):
        for i in range(len(t1), len(t2)):
            t1.append(0)
    elif len(t2) < len(t1):
        for i in range(len(t2), len(t1)):
            t2.append(0)

    if compare == '<':
        return operator.lt(t1, t2)
    elif compare == '<=':
        return operator.le(t1, t2)
    elif compare == '=' or compare == '==':
        return operator.eq(t1, t2)
    elif compare == '!=':
        return operator.ne(t1, t2)
    elif compare == '>=':
        return operator.ge(t1, t2)
    elif compare == '>':
        return operator.gt(t1, t2)
    else:
        raise ValueError('Invalid operator')


def __normalize_version(version):
    v = version.lower()
    v = v.replace('-', '.')
    v = v.replace('_', '.')
    v = v.replace('+', '.')

    fixed_version = ''
    last_was_digit = True
    for char in v:
        if (char.isdigit() or char == '.') and not last_was_digit:
            fixed_version += '.'
            last_was_digit = True
        elif not (char.isdigit() or char == '.') and last_was_digit:
            fixed_version += '.'
            last_was_digit = False
        fixed_version += char

    v = fixed_version

    while '..' in v:
        v = v.replace('..', '.')

    if v[:1] == '.':
        v = v[1:]
    if v[-1:] == '.':
        v = v[:-1]

    return map(__prepare_tuple, v.split("."))


def __prepare_tuple(item):
    """
    Replaces strings with integers, so we can compare them correctly:
    any string not found in this list < dev < alpha = a < beta = b < RC = rc < #

    :param item:
    :return:
    """
    if item == 'dev':
        return -4
    if item == 'a' or item == 'alpha':
        return -3
    if item == 'b' or item == 'beta':
        return -2
    if item == 'rc':
        return -1
    if item.isdigit():
        return int(item)
#    if item == 'pl' or item == 'p':
#        return sys.maxsize

    # Any other string that is no number string
    return -5


if __name__ == "__main__":

    def assert_version_compare(v1, operator, v2, result):
        if version_compare(v1, operator, v2) == result:
            print('[PASS] Comparing %s %s %s' % (v1, operator, v2))
        else:
            print('[ERROR] Comparing %s %s %s' % (v1, operator, v2))

    assert_version_compare('2.1.0alpha1', '<', '2.1.0beta1', True)
    assert_version_compare('2.1.0alpha1', '<=', '2.1.0beta1', True)
    assert_version_compare('2.1.0alpha1', '=', '2.1.0beta1', False)
    assert_version_compare('2.1.0alpha1', '>=', '2.1.0beta1', False)
    assert_version_compare('2.1.0alpha1', '>', '2.1.0beta1', False)

    assert_version_compare('2.1.0beta1', '<', '2.1.0rc1', True)
    assert_version_compare('2.1.0beta1', '<=', '2.1.0rc1', True)
    assert_version_compare('2.1.0beta1', '=', '2.1.0rc1', False)
    assert_version_compare('2.1.0beta1', '>=', '2.1.0rc1', False)
    assert_version_compare('2.1.0beta1', '>', '2.1.0rc1', False)

    assert_version_compare('2.1.0rc1', '<', '2.1.0', True)
    assert_version_compare('2.1.0rc1', '<=', '2.1.0', True)
    assert_version_compare('2.1.0rc1', '=', '2.1.0', False)
    assert_version_compare('2.1.0rc1', '>=', '2.1.0', False)
    assert_version_compare('2.1.0rc1', '>', '2.1.0', False)

    assert_version_compare('2.1.0', '<', '2.1.0', False)
    assert_version_compare('2.1.0', '<=', '2.1.0', True)
    assert_version_compare('2.1.0', '=', '2.1.0', True)
    assert_version_compare('2.1.0', '>=', '2.1.0', True)
    assert_version_compare('2.1.0', '>', '2.1.0', False)

    assert_version_compare('2.1.0', '<', '2.1', False)
    assert_version_compare('2.1.0', '<=', '2.1', True)
    assert_version_compare('2.1.0', '=', '2.1', True)
    assert_version_compare('2.1.0', '>=', '2.1', True)
    assert_version_compare('2.1.0', '>', '2.1', False)

    assert_version_compare('2.1.1', '<', '2.1.0', False)
    assert_version_compare('2.1.1', '<=', '2.1.0', False)
    assert_version_compare('2.1.1', '=', '2.1.0', False)
    assert_version_compare('2.1.1', '>=', '2.1.0', True)
    assert_version_compare('2.1.1', '>', '2.1.0', True)

    assert_version_compare('2.1.1', '<', '2.1', False)
    assert_version_compare('2.1.1', '<=', '2.1', False)
    assert_version_compare('2.1.1', '=', '2.1', False)
    assert_version_compare('2.1.1', '>=', '2.1', True)
    assert_version_compare('2.1.1', '>', '2.1', True)

