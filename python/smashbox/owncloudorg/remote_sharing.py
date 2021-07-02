from owncloud import HTTPResponseError
from smashbox.script import config
from smashbox.utilities import *


def remote_share_file_with_user(filename, sharer, sharee, **kwargs):
    """ Shares a file with a user

    :param filename: name of the file being shared
    :param sharer: the user doing the sharing
    :param sharee: the user receiving the share
    :param kwargs: key words args to be passed into the api, usually for share permissions
    :returns: share id of the created share

    """
    from owncloud import ResponseError

    logger.info('%s is sharing file %s with user %s', sharer, filename, sharee)

    oc_api = get_oc_api()
    oc_api.login(sharer, config.oc_account_password)

    kwargs.setdefault('remote_user', True)
    sharee = "%s@%s" % (sharee, oc_api.url)

    try:
        share_info = oc_api.share_file_with_user(filename, sharee, **kwargs)
        logger.info('share id for file share is %s', str(share_info.share_id))
        return share_info.share_id
    except ResponseError as err:
        logger.info('Share failed with %s - %s', str(err), str(err.get_resource_body()))
        if err.status_code == 403 or err.status_code == 404:
            return -1
        else:
            return -2


def list_open_remote_share(sharee):
    """ Accepts a remote share

    :param sharee: user who created the original share
    """
    logger.info('Listing remote shares for user %s', sharee)

    oc_api = get_oc_api()
    oc_api.login(sharee, config.oc_account_password)
    try:
        open_remote_shares = oc_api.list_open_remote_share()
    except HTTPResponseError as err:
        logger.error('Share failed with %s - %s', str(err), str(err.get_resource_body()))
        if err.status_code == 403 or err.status_code == 404:
            return -1
        else:
            return -2

    return open_remote_shares


def accept_remote_share(sharee, share_id):
    """ Accepts a remote share

    :param sharee: user who created the original share
    :param share_id: id of the share to be accepted

    """
    logger.info('Accepting share %i for user %s', share_id, sharee)

    oc_api = get_oc_api()
    oc_api.login(sharee, config.oc_account_password)
    error_check(oc_api.accept_remote_share(share_id), 'Accepting remote share failed')


def decline_remote_share(sharee, share_id):
    """ Delines a remote share

    :param sharer: user who created the original share
    :param share_id: id of the share to be declined

    """
    logger.info('Declining share %i from user %s', share_id, sharee)

    oc_api = get_oc_api()
    oc_api.login(sharee, config.oc_account_password)
    error_check(oc_api.decline_remote_share(share_id), 'Accepting remote share failed')