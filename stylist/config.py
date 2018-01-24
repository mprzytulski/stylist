import anyconfig
from os import path

from schema import Schema, And, Use, Optional


def stages_conformer(stages): return stages + ['local']


def stylist_conformer(config):
    config.update(config.get('stylist', {}))
    config.pop('stylist', None)
    return config


schema = {Optional('stylist'): {'provider': {'prefix': str, 'type': str},
                                'stages': And(list, Use(stages_conformer))},
          'sentry': {'auth_token': str, 'org': str, 'team': str}}

schema_conformer = And(schema, Use(stylist_conformer))

conform = Schema(schema_conformer, ignore_extra_keys=True).validate


def get(config_file):
    rel_path = path.join('.stylist', config_file)
    return anyconfig.load([path.join('/etc/stylist/', config_file),
                           path.join(path.expanduser('~'), rel_path),
                           rel_path],
                          ignore_missing=True,
                          ac_parser="yaml")
