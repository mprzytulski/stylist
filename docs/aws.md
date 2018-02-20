# AWS Integration
Stylist has been developed as an automation tool for AWS development and deployment, it has integration with following AWS services: 

- Elastic Container Service
- Elastic Container Registry
- Key Management Service
- Relational Database Service
- Systems Manager Parameter Store

## Setting up integration
Stylist use AWS named profiles, you can read more about those here: https://docs.aws.amazon.com/cli/latest/userguide/cli-multiple-profiles.html

By default stylist will map its own profile to AWS configuration profile, but it's possible to use additional `prefix`  which will enable support for `multi-tenancy`. You can read more about setting up prefix in [configuration file documentation](configuration_file.md).