from os import path

import anyconfig
from schema import Schema, And, Optional

schema = {Optional('stylist'): {Optional('provider'): {'prefix': str, 'type': str},
                                Optional('stages'): list,
                                Optional('name_exclusion'): list},
          Optional('sentry'): {'auth_token': str, 'org': str, 'team': str},
          Optional('terraform'): {Optional('templates'): str},
          Optional('docker_images'): {'python3_lambda': str}}

schema_conformer = And(schema)

conform = Schema(schema_conformer, ignore_extra_keys=True).validate


def get(config_file, config_filename):
    return anyconfig.load([path.join('/etc/stylist/', config_filename),
                           path.join(path.expanduser('~'), '.stylist', config_filename),
                           config_file],
                          ignore_missing=True,
                          ac_parser="yaml")
