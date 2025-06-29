# TERRAFORM CONFIGURATION DEPRECATED

## Important Notice

The Terraform configurations in this directory have been **DEPRECATED** and are no longer maintained or used for deployment. They are kept for reference purposes only.

## Transition to AWS CLI

All deployment processes have been migrated to use AWS CLI directly via the `deploy_aws_cli.sh` script in the parent directory. This change was made to:

1. Simplify the deployment process
2. Avoid issues with Terraform provider timeouts and unsupported resource types
3. Provide more direct control over AWS resource creation

## New Deployment Process

Please refer to the main `README.md` file in the parent directory for instructions on using the new AWS CLI-based deployment process.

## Migration Date

These Terraform configurations were deprecated on June 29, 2025.
