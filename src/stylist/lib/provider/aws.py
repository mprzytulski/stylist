import boto3

from stylist.lib.provider import Provider


class AWSProvider(Provider):
    name = "aws"

    known_params = {
        "profile": ("AWS cli profile name", {"type": str, "default": "default"}),
        "kms_key": ("KMS Encryption key id", {"type": str, "default": None}),
    }

    @property
    def session(self):
        return boto3.Session(profile_name=self.profile)
