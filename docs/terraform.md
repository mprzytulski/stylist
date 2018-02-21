# Terraform integration

One of the core features of stylist is automation of the infrastructure management with terraform.

## Concepts
Currently stylist uses default terraform configuration with state files stored in local files - 
there is a plan to move those files into external storage to solve some security issues as well merging problems. 

Stylist will ensure that every terraform command is executed in context of current profile. 

### Directory structure
```  
./terraform/
├── env.*.tfvars
├── module.*.tf
├── provider.tf
├── terraform.tfstate.d
│   ├── *
│   │   ├── terraform.tfstate
│   │   └── terraform.tfstate.backup
│   ├── staging
│   │   ├── terraform.tfstate
│   │   └── terraform.tfstate.backup
│   └── uat
│       ├── terraform.tfstate
│       └── terraform.tfstate.backup
└── variables.tf  
```

- **env.*.tfvars** - environment specific variables 
- **module.*.tf** - autogenerate module inclusion files (see configure-module below)
- **terraform.tfstate.d** - internal terraform directory with all stages and state files
- **./terraform/** - internal terraform cache directory 

### Execution stack
Stylist by default enforce usage of newest infrastructure templates and proper stage selection, to do so every 
terraform command is prepended with two additional commands:

- `terraform init --upgrade=true` to enforce plugins and templates update 
- `terraform workspace select <profile>` to select same workspace as current stylist active profile 

Additionally to speed things up, update command is executed only after an hour from last update for given project. 

### Terraform modules
Stylist is distributed with predefined set of terraform templates, which makes day to day work much simpler. 
Those templates have been build with following assumptions:

- All names of resources are build using project name as a template
- When needed module will include default domain name (see Integration configuration)
- All resources which must have globally unique name like S3 bucket or DNS domain name will include environment name included by default

## Enable terraform project support
`stylist project add-feature terraform`

### Integration configuration
Terraform integration relays on set of the terraform modules which are distributed by default with stylist, but it 
is possible to specify your own location of the modules.
Stylist is able to work with local and remote (via git) locations and to speed things up it will keep local cache of 
the repository in case if git location has been provided. 

If you like to specify your own location for terraform modules you need to add a terraform section to your stylist config file:

```yaml
terraform:
  templates: <path-to-templates>
```

Stylist will automatically recognise if thats a local or remote location.

## Context variable
Some of the modules relays on data which aren't exposed to terraform by default.
In our scenario we use one main repository for shared infrastructure and we keep project specific configuration 
in project repository. It solves some problem and create new ones, one of the problems is that not all resources are 
available to terraform. To workaround that problem we pull that data in stylist and inject those as a part of context.

### List of variables passed as a part of context variable 
- aws_account_id
- aws_region
- aws_profile
- environment 
- project_name

Additionally we inject some variables with auto generated names, those includes:
- Elastic LoadBalancer listener arn's (`alb_<loadbalancer-name>_arn_<http|https>`)
- Api Gateway ID's (`api_<api_name>`)

## List all available modules
`stylist terraform list-modules`

## Configure terraform module
Stylist is able to automatically use terraform modules and provide interactive configuration keeping naming 
conventions and utilising global variables for the configuration if needed.

For example let's add S3 bucket to our project:

```  
stylist terraform configure-module s3_bucket something
```

You will be prompted for values of the module configuration parameters. In most of the cases you may accept default 
values. You can edit that file later as well.

As a result you will will have a terraform module file named `terraform/module.s3_bucket_somthing.tf`.

As you may notice file name is a pattern based: `module.<name-of-the-module>_<alias>.tf`

Thanks to that pattern it's quite easy to see which modules are used by given project.

## Review execution plan
You can safely check terraform execution plan by running:
```  
stylist terraform plan
```

## Apply execution plan
Stylist help as well with applying a plan, to do so - just run
```  
stylist terraform apply
```

It's safe as stylist will first create a plan using `terraform plan` and will allow you to review it before execution. 

## FAQ.

### Terraform use old modules
Run `stylist terraform plan --force-update` or delete `terraform/.tfupdate` file to force module update

### What is `var.context`?
It's a special variable passed to terraform plan with additional informations collected from environment and other 
components, it contain active profile as well as some AWS specific variables like account_id, AWS named profile etc. 
You can read more in context variable section

### Error: Failed to load root config module
You probably added a new module configuration, terraform needs to download it. See: Terraform use old modules
