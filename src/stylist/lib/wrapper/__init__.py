from __future__ import print_function

import json
from datetime import datetime

from memory_profiler import memory_usage

from stylist.lib.aws import TrackerContext


def execute(get_handler, event, ctx):
    def mocked_kms_decrypt(value):
        return value

    try:
        import lambda_utils
        lambda_utils.kms_decrypt = mocked_kms_decrypt
    except ImportError:
        pass

    fn, module = get_handler()

    events = {}
    with TrackerContext(module, events) as tracker:
        startTime = datetime.now()
        # result = fn(event, ctx)
        mem, result = memory_usage((fn, (event, ctx),), retval=True, interval=1e-6)
        execution_time = datetime.now() - startTime

    print(json.dumps({
        "result": result,
        "events": events,
        "stats": {
            "memory": str(max(mem)) + " MB",
            "time": str(execution_time.microseconds / 1000) + " ms"
        }
    }))



