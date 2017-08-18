from stylist.lib.wrapper.tracker import Tracker


class RequestsTracker(Tracker):
    def __init__(self):
        super(RequestsTracker, self).__init__("requests")
        self._requests = None

    def applicable(self, obj):
        return hasattr(obj, "__name__") and obj.__name__ == "requests"

    def apply(self, mocker, c):
        self.spy(mocker, c, "post")
        self.spy(mocker, c, "get")
        self.spy(mocker, c, "put")
        self.spy(mocker, c, "delete")
        self.spy(mocker, c, "head")
