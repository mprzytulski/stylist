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
    def get_parameters(self, *paths):
        """Return all parameters from given namespaces"""

    @abstractmethod
    def write(self, name, value, encrypt=True, tags=None):
        """Write value for given parameter"""

    @abstractmethod
    def delete(self, name):
        """Delete given parameter"""


class DockerRepositoryProvider(object):
    __metaclass__ = ABCMeta
