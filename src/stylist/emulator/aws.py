import json


class Emulator(object):
    def __init__(self, mode, data, lambda_function):
        self.lambda_function = lambda_function
        if isinstance(data, dict):
            self.data = data
        else:
            self.data = json.loads(data)

        if mode == "auto":
            self.mode = self._guess()
        else:
            self.mode = mode

    def emulate(self):
        if self.mode == "sns":
            data = self._sns()
        elif self.mode == "api-gw":
            data = self._api_gw()
        else:
            data = self._direct()

        return json.dumps(data)

    def _api_gw(self):
        return {
            "body": json.dumps(self.data),
            "httpMethod": "POST"
        }

    def _sns(self):
        return {
            "Records": [{
                "Sns": {
                    "Message": self.data
                }
            }]
        }

    def _direct(self):
        return self.data

    def _guess(self):
        triggers = self.lambda_function.config.get("events", {})
        if not len(triggers):
            return "direct"

        if "http" in triggers[0]:
            return "api-gw"
        elif "sns" in triggers[0]:
            return "sns"

        return "direct"
