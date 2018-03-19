import base64


class KMSException(Exception):
    pass


class KMS(object):
    def __init__(self, stylist, key='parameter_store_key', aws=None, session=None):
        if not aws and not session:
            raise KMSException('You need to provide session or AWSProvider instance')

        self.stylist = stylist
        self.key = key

        if not session:
            session = aws.get_session(self.stylist.profile)

        self.session = session
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

    def list_aliases(self, aws=False):
        """
        :param aws: Include AWS build-in aliases
        :return:
        """
        return filter(
            lambda x: (x.get('AliasName').startswith('alias/aws') and aws) or not x.get('AliasName').startswith('alias/aws'),
            self.kms.list_aliases().get('Aliases')
        )

    def encrypt(self, value, key=None):
        key_id = self.get_key_by_alias(key or self.key)
        response = self.kms.encrypt(
            KeyId=key_id,
            Plaintext=bytes(value),
        )

        return base64.b64encode(response.get("CiphertextBlob")), key_id

    def decrypt(self, encrypted):
        try:
            return self.kms.decrypt(
                CiphertextBlob=base64.b64decode(encrypted)
            ).get('Plaintext').decode("utf-8")
        except Exception as e:
            raise KMSException('Failed to decrypt given value')
