import os
import yaml
import collections

from os.path import expanduser
from schema import Schema


class Config(object):
    _dir_in_home = '.threads'
    _config_file_name = 'config.yml'

    def __init__(self, schema):
        self._value = self._merge(self._dir_in_home, self._config_file_name)
        Schema(schema, ignore_extra_keys=True).validate(self._value)

    def __getitem__(self, key):
        return self._value[key]

    @classmethod
    def _deep_update(cls, source, overrides):
        """Update a nested dictionary or similar mapping.

        Modify ``source`` in place.
        """
        for key, value in overrides.iteritems():
            if isinstance(value, collections.Mapping) and value:
                returned = cls._deep_update(source.get(key, {}), value)
                source[key] = returned
            else:
                source[key] = overrides[key]
        return source

    @staticmethod
    def _read(config_filename):
        try:
            with open(config_filename, 'r') as stream:
                try:
                    return yaml.load(stream)
                except IOError:
                    pass
                except yaml.YAMLError as exc:
                    print(exc)
        except IOError as ex:
            return {}

    @classmethod
    def _merge(cls, dir_in_path, config_file_name):
        home_config_file_path = os.path.join(expanduser('~'), dir_in_path, config_file_name)
        proj_config_file_path = os.path.join(os.getcwd(), '.' + config_file_name)
        config = cls._read(home_config_file_path)
        return cls._deep_update(config, cls._read(proj_config_file_path))
