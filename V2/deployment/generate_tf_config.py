#!/usr/bin/env python3
"""
Generate Terraform configurations from the RevOps AI Framework config files.
This script reads the deployment configuration and generates Terraform configuration files.
"""

import os
import json
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_file):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_file}: {str(e)}")
        raise

def generate_tfvars(config, output_path):
    """Generate terraform.tfvars file"""
    tfvars_content = []
    
    # Basic AWS settings
    tfvars_content.append(f'aws_region = "{config.get("aws_region", "us-east-1")}"')
    tfvars_content.append(f'aws_account_id = "{config.get("aws_account_id", "")}"')
    tfvars_content.append(f'environment = "{config.get("environment", "development")}"')
    
    # Secrets configuration
    tfvars_content.append(f'firebolt_credentials_secret = "{config.get("firebolt_credentials_secret", "firebolt-credentials")}"')
    tfvars_content.append(f'webhook_url_secret = "{config.get("webhook_url_secret", "webhook-urls")}"')
    
    # Write to file
    tfvars_path = os.path.join(output_path, 'terraform.tfvars')
    with open(tfvars_path, 'w') as f:
        f.write('\n'.join(tfvars_content))
    
    logger.info(f"Generated Terraform variables file: {tfvars_path}")

def generate_backend_config(config, output_path):
    """Generate backend.tf file for remote state"""
    if "terraform_backend" not in config:
        logger.info("No Terraform backend configuration found, skipping backend.tf generation")
        return
    
    backend_config = config["terraform_backend"]
    
    backend_content = [
        'terraform {',
        '  backend "s3" {'
    ]
    
    for key, value in backend_config.items():
        backend_content.append(f'    {key} = "{value}"')
    
    backend_content.extend([
        '  }',
        '  required_providers {',
        '    aws = {',
        '      source  = "hashicorp/aws"',
        '      version = "~> 5.0"',
        '    }',
        '  }',
        '}',
        '',
        'provider "aws" {',
        '  region = var.aws_region',
        '}'
    ])
    
    # Write to file
    backend_path = os.path.join(output_path, 'backend.tf')
    with open(backend_path, 'w') as f:
        f.write('\n'.join(backend_content))
    
    logger.info(f"Generated Terraform backend configuration: {backend_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate Terraform configurations from RevOps AI Framework config')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    parser.add_argument('--output', default='terraform', help='Output directory for Terraform files')
    parser.add_argument('--secrets', default='secrets.json', help='Path to secrets file')
    parser.add_argument('--deploy-state', default='deploy_state.json', help='Path to deployment state file')
    
    args = parser.parse_args()
    
    try:
        # Ensure output directory exists
        os.makedirs(args.output, exist_ok=True)
        
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        
        # Generate terraform.tfvars
        generate_tfvars(config, args.output)
        
        # Generate backend.tf
        generate_backend_config(config, args.output)
        
        logger.info("Terraform configuration generation complete!")
        
    except Exception as e:
        logger.error(f"Error generating Terraform configuration: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
