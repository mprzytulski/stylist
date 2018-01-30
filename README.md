# Stylist

## Install
[Install Apex](http://apex.run/#installation) to deploy when using `stylist apex deploy`.

```
pip install git+ssh://git@github.com/ThreadsStylingLtd/stylist.git
```

## Environment
Create a configuration in `~/.stylist/config.yml` or `/etc/stylist/config.yml`:
```yaml
sentry:
  auth_token: 133a8ba424da4952a7e2b246de05f16618007cc346caad90a11a31889ee14c1
  org: threads-styling-ltd
  team: threads-styling-ltd
```
The `auth_token` example above is not correct - you need to create your own.
Create an authorization token through
[https://sentry.io/api/](https://sentry.io/api/), with scopes of `project:admin`,
`project:write`, and `org:read`.

The `org` and `team` examples are correct at the time of writing.

## Usage
```
stylist --help
```

## Testing
```
nosetests -a '!clutter' tests
```

## Functionality

* [Profile management](docs/profiles.md)
* [Serverless](docs/serverless.md)
