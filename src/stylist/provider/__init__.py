from abc import ABCMeta, abstractmethod


class Provider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_params(self):
        pass


class AWSProvider(Provider):
    def get_params(self):
        return {
            "profile": ("AWS cli profile name", {"type": str, "default": "default"})
        }

    def verify_params(self, params):
        return True

    def merge_params(self, params=None):
        return {}


def get(name):
    if name == "aws":
        return AWSProvider()

    return None
