import owncloud

__author__ = 'nickv'


class LockProvider:
    LOCK_SHARED = 1
    LOCK_EXCLUSIVE = 2

    def __init__(self, oc_api):
        """
        :param oc_api owncloud.Client
        """
        self.oc_api = oc_api

    def enable_testing_app(self):
        try:
            self.oc_api.make_ocs_request(
                'POST',
                'cloud',
                'apps/testing'
            )
        except owncloud.ResponseError as err:
            raise err

    def disable_testing_app(self):
        try:
            self.oc_api.make_ocs_request(
                'DELETE',
                'cloud',
                'apps/testing'
            )
        except owncloud.ResponseError as err:
            raise err

    def isUsingDBLocking(self):
        try:
            kwargs = {'accepted_codes': [100, 501, 999]}
            res = self.oc_api.make_ocs_request(
                'GET',
                'apps/testing/api/v1',
                'lockprovisioning',
                **kwargs
            )

            import xml.etree.ElementTree as ET
            tree = ET.fromstring(res.content)
            code_el = tree.find('meta/statuscode')

            return int(code_el.text) == 100

        except owncloud.ResponseError as err:
            raise err


    def lock(self, lock_level, user, path):
        """
        Lock the path for the given user

        :param lock_level: 1 (shared) or 2 (exclusive)
        :param user: User to lock the path
        :param path: Path to lock
        :raises: ResponseError if the path could not be locked
        """
        try:
            self.oc_api.make_ocs_request(
                'POST',
                'apps/testing/api/v1',
                'lockprovisioning/%i/%s?path=%s' % (lock_level, user, path)
            )
        except owncloud.ResponseError as err:
            raise err

    def change_lock(self, lock_level, user, path):
        """
        Change an existing lock

        :param lock_level: 1 (shared) or 2 (exclusive)
        :param user: User to lock the path
        :param path: Path to lock
        :raises: ResponseError if the lock could not be changed
        """
        try:
            self.oc_api.make_ocs_request(
                'PUT',
                'apps/testing/api/v1',
                'lockprovisioning/%i/%s?path=%s' % (lock_level, user, path)
            )
        except owncloud.ResponseError as err:
            raise err

    def is_locked(self, lock_level, user, path):
        """
        Check whether the path is locked

        :param lock_level: 1 (shared) or 2 (exclusive)
        :param user: User to lock the path
        :param path: Path to lock
        :returns bool
        """
        try:
            kwargs = {'accepted_codes':  [100, 423]}
            res = self.oc_api.make_ocs_request(
                'GET',
                'apps/testing/api/v1',
                'lockprovisioning/%i/%s?path=%s' % (lock_level, user, path),
                **kwargs
            )

            import xml.etree.ElementTree as ET
            tree = ET.fromstring(res.content)
            code_el = tree.find('meta/statuscode')

            return int(code_el.text) == 100

        except owncloud.ResponseError as err:
            raise err

    def unlock(self, lock_level=None, user=None, path=None):
        """
        Remove all set locks

        :param lock_level: 1 (shared) or 2 (exclusive)
        :param user: User to unlock the path
        :param path: Path to unlock
        :raises: ResponseError if the lock could not be removed
        """
        ocs_path = 'lockprovisioning'

        if lock_level is not None:
            ocs_path = '%s/%i' % (ocs_path, lock_level)

            if user is not None:
                ocs_path = '%s/%s?path=%s' % (ocs_path, user, path)

        try:
            self.oc_api.make_ocs_request(
                'DELETE',
                'apps/testing/api/v1',
                ocs_path
            )
        except owncloud.ResponseError as err:
            raise err
