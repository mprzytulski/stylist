import os
import pkgutil
import importlib


class Feature(object):
    pass


FEATURES = {}


def get_feature(name):
    return FEATURES.get(name)


pkgpath = os.path.dirname(__file__)
for x, name, y in pkgutil.iter_modules([pkgpath]):
    try:
        cls = name.title() + 'Feature'
        module_name = __name__ + '.' + name
        m = importlib.import_module(module_name)
        FEATURES[name] = getattr(m, cls)()
    except ImportError as e:
        raise e
        pass
