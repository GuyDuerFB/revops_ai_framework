#!/usr/bin/env python3
"""
AWS CLI-based Agent Manager for RevOps AI Framework

This script provides reliable agent management functions using AWS CLI commands directly.
Use this as a fallback when the regular deployment scripts encounter issues.
"""

import os
import json
import sys
import subprocess
import logging
from typing import Dict, Any, Optional, List

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to config.json"""
    try:
        # Create backup of current config
        backup_path = os.path.join(PROJECT_ROOT, "backups", f"config.json.{os.path.getmtime(CONFIG_PATH):.0f}")
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        subprocess.run(["cp", CONFIG_PATH, backup_path], check=True)
        
        # Save new config
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def run_aws_cli_command(command: List[str], profile: str, region: str) -> Dict[str, Any]:
    """Run AWS CLI command and return the JSON response"""
    try:
        # Add profile and region to command
        full_command = command + ["--profile", profile, "--region", region]
        logger.info(f"Running AWS CLI command: {' '.join(full_command)}")
        
        # Run command and capture output
        result = subprocess.run(
            full_command, 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Parse JSON response
        if result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse JSON response: {result.stdout}")
                return {"raw_output": result.stdout}
        return {}
    except subprocess.CalledProcessError as e:
        logger.error(f"AWS CLI command failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return {"error": str(e), "stderr": e.stderr}
    except Exception as e:
        logger.error(f"Error running AWS CLI command: {e}")
        return {"error": str(e)}

def list_agents(profile: str, region: str) -> List[Dict[str, Any]]:
    """List all AWS Bedrock agents"""
    response = run_aws_cli_command(
        ["aws", "bedrock-agent", "list-agents"], 
        profile, 
        region
    )
    agents = response.get("agents", [])
    
    if agents:
        logger.info(f"Found {len(agents)} agents:")
        for agent in agents:
            logger.info(f"  Agent ID: {agent.get('agentId')}, Name: {agent.get('displayName')}")
    else:
        logger.info("No agents found")
    
    return agents

def get_agent_details(agent_id: str, profile: str, region: str) -> Dict[str, Any]:
    """Get details about a specific agent"""
    response = run_aws_cli_command(
        ["aws", "bedrock-agent", "get-agent", "--agent-id", agent_id],
        profile,
        region
    )
    
    agent = response.get("agent", {})
    if agent:
        logger.info(f"Agent details:")
        logger.info(f"  Name: {agent.get('displayName')}")
        logger.info(f"  Status: {agent.get('status')}")
        logger.info(f"  Created: {agent.get('createdAt')}")
    else:
        logger.info(f"No details found for agent ID: {agent_id}")
    
    return agent

def list_agent_aliases(agent_id: str, profile: str, region: str) -> List[Dict[str, Any]]:
    """List aliases for an agent"""
    response = run_aws_cli_command(
        ["aws", "bedrock-agent", "list-agent-aliases", "--agent-id", agent_id],
        profile,
        region
    )
    
    aliases = response.get("agentAliasSummaries", [])
    if aliases:
        logger.info(f"Found {len(aliases)} aliases for agent {agent_id}:")
        for alias in aliases:
            logger.info(f"  Alias ID: {alias.get('agentAliasId')}, Name: {alias.get('agentAliasName')}")
    else:
        logger.info(f"No aliases found for agent ID: {agent_id}")
    
    return aliases

def create_agent_alias(agent_id: str, alias_name: str, routing_strategy: str, 
                      description: str, profile: str, region: str) -> Dict[str, Any]:
    """Create an agent alias"""
    response = run_aws_cli_command([
        "aws", "bedrock-agent", "create-agent-alias",
        "--agent-id", agent_id,
        "--agent-alias-name", alias_name,
        "--routing-configuration", f"routingStrategy={routing_strategy}",
        "--description", description
    ], profile, region)
    
    alias = response.get("agentAlias", {})
    if alias:
        logger.info(f"Created agent alias: {alias.get('agentAliasId')}")
    else:
        error = response.get("error", "Unknown error")
        logger.error(f"Failed to create agent alias: {error}")
    
    return alias

def update_config_with_agent_details(agent_type: str, agent_id: str, 
                                   alias_id: Optional[str] = None) -> bool:
    """Update the config.json with agent details"""
    config = load_config()
    
    if agent_type in config:
        config[agent_type]["agent_id"] = agent_id
        if alias_id:
            config[agent_type]["agent_alias_id"] = alias_id
        
        logger.info(f"Updated config for {agent_type} with agent ID: {agent_id}, alias ID: {alias_id}")
        return save_config(config)
    else:
        logger.error(f"Agent type {agent_type} not found in configuration")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python aws_cli_agent_manager.py <command> [options]")
        print("Commands:")
        print("  list-agents                 - List all agents")
        print("  get-agent <agent-id>        - Get details about a specific agent")
        print("  list-aliases <agent-id>     - List aliases for an agent")
        print("  create-alias <agent-id> <alias-name> - Create an alias for an agent")
        print("  update-config <agent-type> <agent-id> [alias-id] - Update config.json")
        return
    
    # Load AWS profile and region from config
    config = load_config()
    profile = config.get("profile_name", "FireboltSystemAdministrator-740202120544")
    region = config.get("region_name", "us-east-1")
    
    command = sys.argv[1]
    
    if command == "list-agents":
        list_agents(profile, region)
    
    elif command == "get-agent":
        if len(sys.argv) < 3:
            print("Error: Agent ID required")
            return
        get_agent_details(sys.argv[2], profile, region)
    
    elif command == "list-aliases":
        if len(sys.argv) < 3:
            print("Error: Agent ID required")
            return
        list_agent_aliases(sys.argv[2], profile, region)
    
    elif command == "create-alias":
        if len(sys.argv) < 4:
            print("Error: Agent ID and alias name required")
            return
        
        agent_id = sys.argv[2]
        alias_name = sys.argv[3]
        routing_strategy = "LATEST"
        description = f"Alias {alias_name} for agent {agent_id}"
        
        alias = create_agent_alias(
            agent_id, alias_name, routing_strategy, description, profile, region
        )
        
        # If alias was created successfully, ask to update config
        if alias and "agentAliasId" in alias:
            agent_type = input("Enter agent type to update in config (data_agent/decision_agent/execution_agent): ")
            if agent_type in ["data_agent", "decision_agent", "execution_agent"]:
                update_config_with_agent_details(agent_type, agent_id, alias["agentAliasId"])
    
    elif command == "update-config":
        if len(sys.argv) < 4:
            print("Error: Agent type and agent ID required")
            return
        
        agent_type = sys.argv[2]
        agent_id = sys.argv[3]
        alias_id = sys.argv[4] if len(sys.argv) > 4 else None
        
        update_config_with_agent_details(agent_type, agent_id, alias_id)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
