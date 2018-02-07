# Stylist

## Install
```
pip install git+ssh://git@github.com/ThreadsStylingLtd/stylist.git
```

## Requirements
[Install Apex](http://apex.run/#installation) to deploy when using `stylist apex deploy`.

To configure the environment with Style, we suggest installing the AWS CLI.

## Usage
```
stylist --help
```

## Testing
```
nosetests -a '!clutter' tests
```

#### Usage
When [configuring AWS named profiles](https://docs.aws.amazon.com/cli/latest/userguide/cli-multiple-profiles.html),
the `<profile>` that should be used when running
`aws configure --profile <profile>` is the same as a Stylist profile.

Refer to **Prefix**.

## Functionality

* [Stylist Concepts](docs/stylist_concepts.md)
* [Config file management](docs/config_files.md)
* Commands:
  * [Project](docs/project.md)
  * [Profile management](docs/profiles.md)
  * [Terraform](docs/terraform.md)
  * [Serverless](docs/serverless.md)
  * TODO Apex (apex init)
  * TODO Docker
