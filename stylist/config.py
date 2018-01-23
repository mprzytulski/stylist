import anyconfig
from os import path

from schema import Schema, And, Use

stages_schema = ['prod', 'uat', 'staging', 'local']


def stages_conformer(stages): return stages + ['local']


def stylist_conformer(config):
    config.update(config.get('stylist', {}))
    del config['stylist']
    return config


schema = {'stylist': {'provider': {'prefix': str, 'type': str},
                      'stages': And(stages_schema, Use(stages_conformer))},
          'sentry': {'auth_token': str, 'org': str, 'team': str}}

schema_conformer = And(schema, Use(stylist_conformer))

validate = Schema(schema, ignore_extra_keys=True).validate


def get(config_file):
    return anyconfig.load([path.join('/etc/stylist/', config_file),
                           path.join(path.expanduser('~'), '/.config/stylist/', config_file),
                           path.join('.stylist/', config_file)],
                          ignore_missing=True,
                          ac_parser="yaml")
