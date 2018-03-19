import re


class ConfigNamespaceException(Exception):
    """Invalid parameter name"""


def resolve_full_name(namespace, parameter=''):
    """
    Convert namespaced parameter notation into log service:news/parameter -> /service/news/parameter
    :param namespace:
    :param parameter:
    :return:
    """
    if not re.match('(service|resource|master):\w+', namespace):
        raise ConfigNamespaceException(
            'Namespace should be one of service, resource, master and followed by name, ex. resource:db'
        )

    return '/' + '/'.join((namespace.replace(':', '/').rstrip('/'), parameter.lstrip('/'))).lower()


def parametrise_name(name):
    """Replace text into unified parameter path value"""
    return re.sub('\W', '-', name)


def normalise_name(name, env_name=False):
    if env_name:
        return re.sub('\W', '_', name.upper()).strip('_')
    else:
        return re.sub('/(service|resource|master)/(.*)', '\\1:\\2', name)


def format_full(param):
    return param


def format_short(param):
    param[0] = normalise_name(param[0])
    return param


def format_env(param):
    param[0] = normalise_name(param[0], True)
    return param


FORMATTER = {
    'full': format_full,
    'short': format_short,
    'env': format_env
}
