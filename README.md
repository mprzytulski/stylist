# Stylist

## QuickStart

Create an authorization token through
[https://sentry.io/api/](https://sentry.io/api/), with scopes of
`project:admin`, `project:write`, and `org:read`. Set the generated
authentication token as a `SENTRY_AUTH_TOKEN` environment variable.

### Install stylist
```
pip install git+ssh://git@github.com/ThreadsStylingLtd/stylist.git
```

### Environment
Create a configuration file `.config.yml` at the root of the project
directory where a `stylist` project is to be created, or in `~/.threads/config.yml`:
```yaml
sentry:
  auth_token: 133a8ba424da4952a7e2b246de05f16618007cc346caad90a11a31889ee14c1
  org: threads-styling-ltd
  team: threads-styling-ltd
```
The `auth_token` example above is not correct - you need to create your own.
The `org` and `team` examples are correct at the time of writing.

### Usage
```
stylist project init
```

## Testing
```
nosetests -a '!clutter' tests
```

## Functionality

* [Profile management](docs/profiles.md)
* [Serverless](docs/serverless.md)
