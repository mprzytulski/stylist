from abc import ABCMeta, abstractmethod


class ConfigStorage(object):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def name(self):
        pass


class DockerRepositoryProvider(object):
    __metaclass__ = ABCMeta
