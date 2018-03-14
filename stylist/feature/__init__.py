import os
from abc import abstractmethod, ABCMeta


class NotProjectDirectoryException(Exception):
    pass


def ensure_project_directory(dir):
    if not os.path.isdir(os.path.join(dir, '.stylist')):
        raise NotProjectDirectoryException("Given directory is not under a stylist control")


class Feature(object):
    __metaclass__ = ABCMeta

    def __init__(self, stylist):
        """

        :param stylist: Stylist
        """
        self.stylist = stylist

    @property
    @abstractmethod
    def installed(self):
        pass

    def load_providers(self):
        """Registry all services"""
        pass

    @abstractmethod
    def _do_setup(self, init_args):
        pass

    def setup(self, init_args):
        if self.installed:
            raise FeatureAlreadyEnabledException()

        return self._do_setup(init_args)


class FeatureException(Exception):
    def __init__(self, message=None, source=None):
        self.message = message
        self.source = source


class FeatureAlreadyEnabledException(FeatureException):
    pass


class FeatureSetupException(FeatureException):
    pass
