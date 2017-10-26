from stylist.lib.wrapper.tracker import Tracker


class SNSTracker(Tracker):
    def __init__(self):
        super(SNSTracker, self).__init__('botocore.client.SNS')

    def apply(self, mocker, c):
        self.spy(mocker, c, "publish")


class ClientTracker(Tracker):
    def __init__(self):
        super(ClientTracker, self).__init__("boto3")
        self._client = None

    def applicable(self, obj):
        return hasattr(obj, "__name__") and obj.__name__ == "boto3"

    def apply(self, mocker, c):
        self._client = c.client

        c.client = self.client

        self.spy(mocker, c, "client")

    def client(self, *args, **kwargs):
        return self._client(*args, **kwargs)
