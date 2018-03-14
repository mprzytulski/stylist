from dependency_injector import providers, containers
import providers as stylist_providers


class ConfigStorageProvider(providers.Factory):
    provided_type = stylist_providers.ConfigStorage


class ConfigStorageContainer(containers.DynamicContainer):
    pass


class GlobalContainer(containers.DynamicContainer):
    pass
