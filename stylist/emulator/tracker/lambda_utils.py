from stylist.lib.wrapper.tracker import Tracker


class LambdaUtilsTracker(Tracker):
    def __init__(self):
        super(LambdaUtilsTracker, self).__init__("lambda_utils")
        self._client = None

    def applicable(self, obj):
        return hasattr(obj, "__name__") and obj.__name__ == "lambda_utils"

    def apply(self, mocker, c):
        print(c)
        self._client = c.client

        c.client = self.client

        self.spy(mocker, c, "client")

    def client(self, *args, **kwargs):
        return self._client(*args, **kwargs)
