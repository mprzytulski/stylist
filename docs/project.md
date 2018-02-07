# "project" command
## "init" sub-command
`stylist project init` initialises a new *Stylist* project.

### Creates Stylist environment files:
`.stylist/config.yml`:
```
stylist:
  provider: {prefix: <maybe_your_org>, type: aws}
  stages: [prod, uat, staging]
```
Stylist supports only one `provider:` - AWS, at the time of writing, but more
may come!

For `prefix:` refer to **Prefix**.  

`.stylist/environment` contains the currently selected `stage`. It allows
Stylist commands to know which stage to target.

### Creates a Sentry integration:
Integrates a git repo with Sentry by setting up a Sentry project and making its
DSN secret available through AWS SSM. The DSN secret is stored in AWS SSM with
its parameter name in following format: `/service/<git_repo>/sentry`.

#### Requirements:
Create a configuration file in `~/.stylist/config.yml` or
`/etc/stylist/config.yml` as such:
```yaml
sentry:
  auth_token: 133a8ba424da4952a7e2b246de05f16618007cc346caad90a11a31889ee14c1
  org: <maybe_your_org>
  team: <maybe_your_team>
```
The `auth_token` example above is not correct - you need to create your own.
Create an authorization token through
[https://sentry.io/api/](https://sentry.io/api/), with scopes of
`project:admin`, `project:write`, and `org:read`.

You should have locally configured credentials to all stages corresponding to
the ones created in `.stylist/config.yml` under:
```
stylist:
    stages: [...]
```
Otherwise the Sentry integration will abort when writing to SSM fails.
This will be fixed very soon, to continue writing to SSM in other stages.  

#### Usage example:
```python
  import boto3
  ssm = boto3.client('ssm')
  param_name = "/service/<git_repo>/sentry"
  ssm.get_parameters(Names=[param_name], WithDecryption=True)
  sentry_dsn_secret = response['Parameters'][0]['Value']
  os.environ['SENTRY_DSN'] = sentry_dsn_secret
  
  @RavenLambdaWrapper()
  def my_lambda_handler():
      # A raised exception would bubble up and get caught here with an event
      # then being sent to Sentry about the exception
```

