# Stylist project

## Initialise a project
`stylist project init .` initialises a new *Stylist* project using a current directory as a base.

After initialisation you may notice a new directory `.stylist` which contain a configuration file `config.yml` 
- you can read more about configuration files [here](configuration_files.md).
Additionally there is one more file `environment` which contain name of the currently selected profile - 
[here](profiles.md) you can find more about profiles.

```  
├── .stylist
│   ├── config.yml
│   └── environment  
```

## Add project feature 
Every stylist project can have multiple features enabled - for example terraform orchestration or sentry integration.
You can add as many features to a project as you like, you can simple call:

```bash
stylist project add-feature sentry
``` 

If given feature will require any additional configuration settings you will be prompted.

## Listing features

```
stylist project list-features

┌STYLIST FEATURES────────────────────────────────────────────────────┬───────────┐
│ FEATURE    │ DESCRIPTION                                           │ INSTALLED │
├────────────┼───────────────────────────────────────────────────────┼───────────┤
│ apex       │ Build and deploy your AWS lambda functions with apex. │ false     │
├────────────┼───────────────────────────────────────────────────────┼───────────┤
│ serverless │                                                       │ false     │
├────────────┼───────────────────────────────────────────────────────┼───────────┤
│ docker     │ Build and manage your docker containers.              │ true      │
├────────────┼───────────────────────────────────────────────────────┼───────────┤
│ sentry     │ Error handling and reporting with sentry / raven.     │ true      │
├────────────┼───────────────────────────────────────────────────────┼───────────┤
│ terraform  │ Orchestrate infrastructure with terraform             │ true      │
└────────────┴───────────────────────────────────────────────────────┴───────────┘
``` 

