import anyconfig
from os import path

from schema import Schema, And, Use, Optional

schema = {Optional('stylist'): {'provider': {'prefix': str, 'type': str},
                                'stages': list,
                                Optional('name_exclusion'): list},
          Optional('sentry'): {'auth_token': str, 'org': str, 'team': str},
          Optional('docker_images'): {'python3_lambda': str}}

schema_conformer = And(schema)

conform = Schema(schema_conformer, ignore_extra_keys=True).validate


def get(config_file, config_filename):
    return anyconfig.load([path.join('/etc/stylist/', config_filename),
                           path.join(path.expanduser('~'), '.stylist', config_filename),
                           config_file],
                          ignore_missing=True,
                          ac_parser="yaml")
