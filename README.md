# Stylist

## QuickStart

Create an authorization token through
[https://sentry.io/api/](https://sentry.io/api/) and set it to
the `SENTRY_AUTH_TOKEN` environment variable.

```
pip install git+ssh://git@github.com/ThreadsStylingLtd/stylist.git
SENTRY_AUTH_TOKEN=<YOUR_SENTRY_AUTH_TOKEN> stylist project init
```

## Testing
```
SENTRY_AUTH_TOKEN=<YOUR_SENTRY_AUTH_TOKEN> nosetests tests/
```

## Functionality

* [Profile management](docs/profiles.md)
* [Serverless](docs/serverless.md)
