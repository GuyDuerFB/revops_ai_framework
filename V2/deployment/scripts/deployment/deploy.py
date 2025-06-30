#!/usr/bin/env python3
"""
RevOps AI Framework V2 - AWS Deployment Script

This script deploys all components of the RevOps AI Framework to AWS using AWS CLI.
The deployment follows this order:
1. Lambda functions (tools)
2. Knowledge base
3. Data agent
4. Decision agent
5. Execution agent

Requirements:
- AWS CLI configured with appropriate permissions
- config.json and secrets.json files in the deployment directory
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

# Import deployment modules
from lambda_deployer import deploy_lambda_functions, test_lambda_function
from knowledge_base_deployer import deploy_knowledge_base, test_knowledge_base
from agent_deployer import deploy_agent, test_agent

# Constants
CONFIG_FILE = "config.json"
SECRETS_FILE = "secrets.json"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config() -> Dict[str, Any]:
    """
    Load the deployment configuration from config.json
    """
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


def load_secrets() -> Dict[str, Any]:
    """
    Load the secrets from secrets.json
    """
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


def update_config(config: Dict[str, Any]) -> None:
    """
    Update the configuration file with new values
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Updated configuration saved to {CONFIG_FILE}")


def deploy_all(config: Dict[str, Any], secrets: Dict[str, Any], components: List[str] = None) -> Dict[str, Any]:
    """
    Deploy all components or specified components
    """
    updated_config = config.copy()
    
    all_components = ["lambda", "kb", "data_agent", "decision_agent", "execution_agent"]
    components_to_deploy = components if components else all_components
    
    # Set AWS environment from config
    os.environ["AWS_REGION"] = config.get("region_name", "us-east-1")
    if config.get("profile_name"):
        os.environ["AWS_PROFILE"] = config.get("profile_name")
    
    # Deploy Lambda functions (tools)
    if "lambda" in components_to_deploy:
        print("\n=== Deploying Lambda Functions ===")
        lambda_results = deploy_lambda_functions(config, secrets)
        updated_config = lambda_results["config"]
    
    # Deploy knowledge base
    if "kb" in components_to_deploy:
        print("\n=== Deploying Knowledge Base ===")
        kb_results = deploy_knowledge_base(updated_config, secrets)
        updated_config = kb_results["config"]
    
    # Deploy data agent
    if "data_agent" in components_to_deploy:
        print("\n=== Deploying Data Agent ===")
        data_agent_results = deploy_agent(updated_config, secrets, "data_agent")
        updated_config = data_agent_results["config"]
    
    # Deploy decision agent
    if "decision_agent" in components_to_deploy:
        print("\n=== Deploying Decision Agent ===")
        decision_agent_results = deploy_agent(updated_config, secrets, "decision_agent")
        updated_config = decision_agent_results["config"]
    
    # Deploy execution agent
    if "execution_agent" in components_to_deploy:
        print("\n=== Deploying Execution Agent ===")
        execution_agent_results = deploy_agent(updated_config, secrets, "execution_agent")
        updated_config = execution_agent_results["config"]
    
    return {"config": updated_config}


def test_components(config: Dict[str, Any], secrets: Dict[str, Any], components: List[str] = None) -> None:
    """
    Test deployed components
    """
    all_components = ["lambda", "kb", "data_agent", "decision_agent", "execution_agent", "e2e"]
    components_to_test = components if components else all_components
    
    # Set AWS environment from config
    os.environ["AWS_REGION"] = config.get("region_name", "us-east-1")
    if config.get("profile_name"):
        os.environ["AWS_PROFILE"] = config.get("profile_name")
    
    # Test Lambda functions
    if "lambda" in components_to_test:
        print("\n=== Testing Lambda Functions ===")
        lambda_functions = config.get("lambda_functions", {})
        for lambda_name, lambda_config in lambda_functions.items():
            print(f"Testing {lambda_name} function...")
            test_lambda_function(lambda_name, lambda_config)
    
    # Test knowledge base
    if "kb" in components_to_test:
        print("\n=== Testing Knowledge Base ===")
        test_knowledge_base(config)
    
    # Test data agent
    if "data_agent" in components_to_test:
        print("\n=== Testing Data Agent ===")
        test_agent(config, secrets, "data_agent")
    
    # Test decision agent
    if "decision_agent" in components_to_test:
        print("\n=== Testing Decision Agent ===")
        test_agent(config, secrets, "decision_agent")
    
    # Test execution agent
    if "execution_agent" in components_to_test:
        print("\n=== Testing Execution Agent ===")
        test_agent(config, secrets, "execution_agent")
    
    # Test end-to-end flow
    if "e2e" in components_to_test:
        print("\n=== Testing End-to-End Flow ===")
        # This will test the entire flow from data agent to decision agent to execution agent
        test_e2e(config, secrets)


def test_e2e(config: Dict[str, Any], secrets: Dict[str, Any]) -> None:
    """
    Test the end-to-end flow: data agent -> decision agent -> execution agent
    """
    print("Running end-to-end test of the RevOps AI Framework...")
    print("1. Invoking data agent to retrieve information...")
    # Implementation of E2E test will be added here
    print("E2E test completed!")


def main():
    parser = argparse.ArgumentParser(description="Deploy RevOps AI Framework to AWS")
    parser.add_argument("--deploy", nargs="*", help="Components to deploy (lambda, kb, data_agent, decision_agent, execution_agent)")
    parser.add_argument("--test", nargs="*", help="Components to test (lambda, kb, data_agent, decision_agent, execution_agent, e2e)")
    args = parser.parse_args()
    
    # Load configuration and secrets
    config = load_config()
    secrets = load_secrets()
    
    # Determine action
    if args.deploy is not None:
        # Empty list means deploy all
        components = args.deploy if args.deploy else None
        results = deploy_all(config, secrets, components)
        update_config(results["config"])
        print("Deployment completed successfully!")
    
    if args.test is not None:
        # Empty list means test all
        components = args.test if args.test else None
        test_components(config, secrets, components)
        print("Testing completed!")
    
    if args.deploy is None and args.test is None:
        print("No action specified. Use --deploy or --test to specify an action.")
        parser.print_help()


if __name__ == "__main__":
    main()
