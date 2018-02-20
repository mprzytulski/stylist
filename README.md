# Stylist
The stylist is an opinionated project development and deployment tool created as a wrapper around well know tools like [terraform](https://terraform.io) or [docker](https://www.docker.com/). Additionally sylist has support for code generation and deployment for well know frameworks like [serverless](https://serverless.com), [apex](https://apex.run) or [chalice](https://github.com/aws/chalice). 

A few main assumptions behind stylist:
- automate as much as possible 
- enforce same naming patterns 
- standardise build and deployment 
- simplify day to day work
- remove the need for local makefiles or other build scripts

## What stylist can do for you
- Build docker containers, upload those to ECS repository and enrol new version using terraform.
- Build and deploy lambda function managed with apex framework - including build of native dependencies via Docker container
- Manage infrastructure with terraform, providing a set of templates for common tasks. Including automation of 
- Manage project configuration with AWS Systems Manager Parameter Store (including sync of variables between multiple stages)
- Manage you databases (including db and user creation, storing permissions in SSM Parameter store and schema migrations ) 

**Disclaimer**: *We use stylist on the daily basis, but it was built to fit our needs and simplify our life here at 
Threads Styling. It has been released as an alpha version for the general public which means that it may require some 
work before you will be able to use it.*

## Install
```
pip install git+ssh://git@github.com/ThreadsStylingLtd/stylist.git
```

### External dependencies
Stylist operates as a wrapper around common tools and frameworks, to be able to use all the features you must ensure that following are installed and available in user `$PATH`:

**Tools**:
- Docker - https://www.docker.com/
- Terraform - https://terraform.io/
- virtualenv - https://packaging.python.org/key_projects/#virtualenv
- pip - https://pip.pypa.io/en/stable/installing/

**Frameworks**:
- apex - https://apex.run
- serverless - https://serverless.com/
- chalice - https://github.com/aws/chalice
- yoyo-migrate - https://pypi.python.org/pypi/yoyo-migrations

## Stylist concepts 

One of the main purposes of stylist is to organise a workflow an ensure consistency between tools and frameworks. 

Stylist operates under context of `project` - in most of the cases project will represent your source code repository. 
Every project can have multiple profiles (staging, uat, production) to which project can be deployed.

- [Project](docs/project.md)
- [AWS Integration](docs/aws.md)
- [Profile management](docs/profiles.md)
- [Configuration](docs/config.md)

## Integrations
- [Terraform](docs/terraform.md)
- [Serverless](docs/serverless.md)
- chalice
- apex
- docker
- DB Migrations with [yoyo](https://bitbucket.org/ollyc/yoyo)

### AWS service support 
- Elastic Container Service
- Elastic Container Registry
- Key Management Service
- Relational Database Service
- Systems Manager Parameter Store

## FAQ
