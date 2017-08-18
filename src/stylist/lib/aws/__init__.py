from __future__ import print_function

import abc
import sys

from pytest_mock import MockFixture


def _get_mock_module():
    """
    Import and return the actual "mock" module. By default this is "mock" for Python 2 and
    "unittest.mock" for Python 3, but the user can force to always use "mock" on Python 3 using
    the mock_use_standalone_module ini option.
    """
    if not hasattr(_get_mock_module, '_module'):
        use_standalone_module = False
        if sys.version_info[0] == 2 or use_standalone_module:
            import mock
            _get_mock_module._module = mock
        else:
            import unittest.mock
            _get_mock_module._module = unittest.mock

    return _get_mock_module._module


class Mocker(MockFixture):
    def __init__(self):
        self._patches = []  # list of mock._patch objects
        self._mocks = []  # list of MagicMock objects
        self.mock_module = mock_module = _get_mock_module()
        self.patch = self._Patcher(self._patches, self._mocks, mock_module)
        # aliases for convenience
        self.Mock = mock_module.Mock
        self.MagicMock = mock_module.MagicMock
        self.PropertyMock = mock_module.PropertyMock
        self.call = mock_module.call
        self.ANY = mock_module.ANY
        self.DEFAULT = mock_module.DEFAULT
        self.sentinel = mock_module.sentinel
        self.mock_open = mock_module.mock_open


class TrackerContext(object):
    trackers = []

    def __init__(self, module, events):
        self.events = events
        self.module = module
        self.mocker = Mocker()
        # mocker.spy(self.boto, 'client')

    def __enter__(self):
        # print(TrackerContext.trackers)
        for key, attr in self.module.__dict__.items():
            for tracker in [t for t in TrackerContext.trackers if t.applicable(attr)]:
                tracker.apply(self.mocker, attr)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for tracker in TrackerContext.trackers:
            self.events[tracker.name] = tracker.events()

    @staticmethod
    def registry(tracker):
        TrackerContext.trackers.append(tracker)


class Tracker(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        super(Tracker, self).__init__()
        self.name = name
        self.tracked = {}

    def is_instance(self, obj, req):
        if not hasattr(obj, '__module__'):
            return False

        fqcn = obj.__module__ + "." + obj.__class__.__name__

        return fqcn == req

    def applicable(self, obj):
        return self.is_instance(obj, self.name)

    def events(self):
        e = {}
        for method, tracked in self.tracked.items():
            if not len(tracked.mock_calls):
                continue
            e.update({
                method: [call[2] for call in tracked.mock_calls]
            })

        return e

    def spy(self, mocker, obj, method):
        mocker.spy(obj, method)

        self.tracked[method] = getattr(obj, method)


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


TrackerContext.registry(SNSTracker())
TrackerContext.registry(ClientTracker())
TrackerContext.registry(LambdaUtilsTracker())
TrackerContext.registry(RequestsTracker())
