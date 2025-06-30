#!/usr/bin/env python3
"""
Script to deploy all Lambda functions except Gong
"""
import json
import os
import sys
from lambda_deployer import deploy_lambda_functions, test_lambda_function
from knowledge_base_deployer import deploy_knowledge_base, test_knowledge_base
from agent_deployer import deploy_agent, test_agent

# Constants
CONFIG_FILE = "config.json"
SECRETS_FILE = "secrets.json"

def load_config():
    """Load the deployment configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {CONFIG_FILE} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {CONFIG_FILE}.")
        sys.exit(1)

def load_secrets():
    """Load the secrets from secrets.json"""
    secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SECRETS_FILE)
    try:
        with open(secrets_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Secrets file {SECRETS_FILE} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {SECRETS_FILE}.")
        sys.exit(1)

def update_config(config):
    """Update the configuration file with new values"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Updated configuration saved to {CONFIG_FILE}")

def deploy_all_except_gong(config, secrets):
    """Deploy all Lambda functions except Gong"""
    updated_config = config.copy()
    
    # Set AWS environment from config
    os.environ["AWS_REGION"] = config.get("region_name", "us-east-1")
    if config.get("profile_name"):
        os.environ["AWS_PROFILE"] = config.get("profile_name")
    
    # Make a copy of the config with Gong removed
    config_without_gong = config.copy()
    if "lambda_functions" in config_without_gong:
        if "gong_retrieval" in config_without_gong["lambda_functions"]:
            print("Excluding 'gong_retrieval' Lambda from deployment.")
            del config_without_gong["lambda_functions"]["gong_retrieval"]
    
    # Deploy Lambda functions (tools) except Gong
    print("\n=== Deploying Lambda Functions (excluding Gong) ===")
    lambda_results = deploy_lambda_functions(config_without_gong, secrets)
    updated_config = lambda_results["config"]
    
    # Restore Gong configuration in the updated config
    if "gong_retrieval" in config["lambda_functions"]:
        updated_config["lambda_functions"]["gong_retrieval"] = config["lambda_functions"]["gong_retrieval"]
    
    return {"config": updated_config}

if __name__ == "__main__":
    # Load configuration and secrets
    config = load_config()
    secrets = load_secrets()
    
    # Deploy all Lambda functions except Gong
    results = deploy_all_except_gong(config, secrets)
    update_config(results["config"])
    
    print("Deployment completed successfully!")
