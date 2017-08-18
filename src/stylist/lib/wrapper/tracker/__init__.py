import abc

from stylist.lib.wrapper.mock import Mocker


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
