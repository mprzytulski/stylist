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

    return '/'.join((namespace.replace(':', '/').rstrip('/'), parameter.lstrip('/'))).lower()


def parametrize_name(name):
    """Replace text into unified parameter path value"""
    return re.sub('\W', '-', name)
