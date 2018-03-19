class KMSException(Exception):
    pass


class KMS(object):
    def __init__(self, stylist, session):
        self.session = session
        self.stylist = stylist
        self.kms = self.session.client("kms")

    def get_key_by_alias(self, alias=None):
        aliases = self.kms.list_aliases()

        key_id = (next(iter(filter(
            lambda x: x.get('AliasName') == 'alias/' + alias,
            aliases.get('Aliases', {})
        ))) or {}).get('TargetKeyId')

        if key_id:
            return key_id

        raise KMSException('Unable to locate KMS key with "{}" alias.'.format(alias))
