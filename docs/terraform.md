# "terraform" command

## "configure-module" sub-command
Creates a terraform module file using its Apex project name and
[one of these templates](https://github.com/ThreadsStylingLtd/templates/tree/master/terraform_modules).

Say we want to create a terraform module based on the `s3_bucket` template.

We have the following Apex generated `project.json` file:
```
$ cat project.json
{
  "name": "my-apex-proj"
}
```
Running
```
my-proj $ stylist terraform configure-module s3_bucket my-apex-proj
```
creates a terraform module file as `terraform/module.s3_bucket_my-apex-proj.tf`.
All the prompted questions do not need to be answered.

The aforementioned file should be edited to be used by your app:
```hcl
module "s3_bucket_my_apex_proj" {


  # Internal stylist variables - do not edit below
  source = "git@github.com:ThreadsStylingLtd/templates.git//terraform_modules/s3_bucket"
  context = "${var.context}"
```
It's common to attach IAM policy resources (sourcing from a Terraform template) to an
Apex generated IAM role as such:
```hcl
  iam_role_name = "parcel-lambda_lambda_function"
```

Refer to the [Terraform documentation](https://www.terraform.io/docs/) to
learn how to edit Terraform files.

After doing all the editing run:
```
stylist terraform apply
```
to apply all the changes to the selected stage environment. 

### Requirements
`stylist apex init` was ran once in the git project. 

### Troubleshooting
**Issue:** Running `configure-module` throws `git.exc.InvalidGitRepositoryError`.

**Fix:** Run `stylist terraform plan --force-update`

