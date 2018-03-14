from abc import ABCMeta, abstractmethod


class ConfigStorage(object):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def get_parameter(self, name):
        """Return value of the parameter for given name"""

    @abstractmethod
    def get_parameters(self, path):
        """Return all parameters from given namespace"""

    @abstractmethod
    def write(self, name, value, encrypt=True):
        """Write value for given parameter"""


class DockerRepositoryProvider(object):
    __metaclass__ = ABCMeta
