# Sentry integration
Stylist provide a small integration with [Sentry](https://sentry.io) - an excellent monitoring tool. 

Currently integration is limited only to creation of the project with corresponding access keys for each project stage.

Stylist will automatically create a project and access keys during project initialisation if sentry has been configured on system or user level.

### Integration configuration
To use sentry integration stylist need to be configured with sentry credentials, it's recommended to setup those on user or system level. 

```yaml
sentry:
  auth_token: <oauth-token>
  org: <organisation-slug>
  team: <tema-slug>
```

Values for all configuration parameters can be obtain from sentry admin console. 

Create an authorisation token through
[https://sentry.io/api/](https://sentry.io/api/), with scopes of
`project:admin`, `project:write`, and `org:read`.

## Enable sentry integration for existing project
It is possible to enable sentry feature for already initialised project.
To do so, simply run:
```
stylist project add-feature sentry
```

## SSM Parameter Store integration
Stylist by default write sentry DSN into SSM project namespace under `sentry` key.

You should have locally configured credentials to all stages corresponding to the ones defined in stylist configuration.

Otherwise the Sentry integration will abort when writing to SSM fails.
