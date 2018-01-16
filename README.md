# Stylist

## QuickStart

Create an authorization token through
[https://sentry.io/api/](https://sentry.io/api/), with scopes of
`project:admin`, `project:write`, and `org:read`. Set the generated
authentication token as a `SENTRY_AUTH_TOKEN` environment variable.

```
pip install git+ssh://git@github.com/ThreadsStylingLtd/stylist.git
SENTRY_AUTH_TOKEN=<YOUR_SENTRY_AUTH_TOKEN> stylist project init
```

## Testing
```
SENTRY_AUTH_TOKEN=<YOUR_SENTRY_AUTH_TOKEN> nosetests -a '!clutter' tests/
```

## Functionality

* [Profile management](docs/profiles.md)
* [Serverless](docs/serverless.md)
