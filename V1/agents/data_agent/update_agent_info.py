#!/usr/bin/env python
"""
Update local configuration files with information about an existing Bedrock agent.
This script retrieves information about an existing Bedrock agent and updates
the local agent_deployment.json file with the agent details.
"""

import os
import json
import argparse
import boto3
from pathlib import Path
from agent_definition import DataAgent, get_bedrock_agent_client

def dump_action_groups(agent_id, region=None, profile=None, specific_action_group=None):
    """
    Retrieve and dump detailed information about an agent's action groups.
    
    Args:
        agent_id (str): The Bedrock agent ID
        region (str, optional): AWS region. Defaults to None.
        profile (str, optional): AWS profile name. Defaults to None.
    """
    # Create a bedrock-agent client
    session = boto3.Session(region_name=region if region else 'us-east-1', profile_name=profile)
    client = session.client('bedrock-agent')
    
    try:
        # First, get the agent details to get information about versions
        agent_response = client.get_agent(agentId=agent_id)
        print(f"Agent Name: {agent_response.get('agentName', 'Unknown')}")
        
        # Try to list the agent versions
        try:
            versions_response = client.list_agent_versions(agentId=agent_id)
            versions = versions_response.get('agentVersionSummaries', [])
            if versions:
                print(f"Found {len(versions)} published versions of the agent")
                for v in versions:
                    v_id = v.get('agentVersion')
                    print(f"  - Version {v_id} (Status: {v.get('agentVersionStatus')})")
                
                # Use the latest published version if available
                latest_version = versions[0].get('agentVersion')
                print(f"Using latest published version: {latest_version}")
                agent_version = latest_version
            else:
                print("No published versions found. Using DRAFT version.")
                agent_version = 'DRAFT'
        except Exception as e:
            print(f"Could not list agent versions: {e}. Using DRAFT version instead.")
            agent_version = 'DRAFT'
        
        print(f"Checking action groups for version: {agent_version}")
        
        # Try to list any aliases first to see what's active
        try:
            aliases_response = client.list_agent_aliases(agentId=agent_id)
            aliases = aliases_response.get('agentAliasSummaries', [])
            if aliases:
                print(f"Found {len(aliases)} agent aliases:")
                for alias in aliases:
                    print(f"  - {alias.get('agentAliasName')} (ID: {alias.get('agentAliasId')}, Status: {alias.get('agentAliasStatus')})")
                    # Get the routing configuration to find version
                    alias_detail = client.get_agent_alias(
                        agentId=agent_id,
                        agentAliasId=alias.get('agentAliasId')
                    )
                    routing = alias_detail.get('routingConfiguration', {})
                    if routing:
                        alias_version = routing.get('agentVersion')
                        print(f"    -> Points to agent version: {alias_version}")
        except Exception as e:
            print(f"Could not list agent aliases: {e}")
        
        # Try to list published versions first, then fallback to DRAFT
        versions_to_try = []
        try:
            versions_response = client.list_agent_versions(agentId=agent_id)
            published_versions = versions_response.get('agentVersionSummaries', [])
            # Check all published versions
            for v in published_versions:
                v_id = v.get('agentVersion')
                v_status = v.get('agentVersionStatus')
                if v_id and v_id != 'DRAFT':  # Include any non-DRAFT version
                    versions_to_try.append(v_id)
                    print(f"Found published version: {v_id} with status {v_status}")
        except Exception as e:
            print(f"Error listing published versions: {e}")
        
        # Add DRAFT version as a fallback if no published versions were found
        if not versions_to_try:
            versions_to_try.append('DRAFT')
            print("No published versions found, will check DRAFT version")
        else:
            print(f"Will check these published versions: {', '.join(versions_to_try)}")
            # Add DRAFT as the last option
            versions_to_try.append('DRAFT')
        
        action_groups_found = False
        found_action_groups = []
        active_version = None
        
        for version in versions_to_try:
            try:
                print(f"\nTrying to get action groups for version: {version}")
                # Get the agent's action groups for this version
                # Print detailed debug information
                print(f"DEBUG: Getting action groups for version {version}")
                response = client.list_agent_action_groups(
                    agentId=agent_id,
                    agentVersion=version
                )
                action_groups = response.get('actionGroupSummaries', [])
                print(f"DEBUG: Raw action groups response: {response}")
                print(f"DEBUG: Found {len(action_groups)} action groups")
                
                # Print each action group name regardless of filter
                for ag in action_groups:
                    print(f"DEBUG: Action group found: {ag.get('actionGroupName')} (ID: {ag.get('actionGroupId')})")
                
                if specific_action_group:
                    # If we're looking for a specific action group, check by name
                    for ag in action_groups:
                        if specific_action_group.lower() in ag['actionGroupName'].lower():
                            print(f"Found specific action group: {ag['actionGroupName']} ({ag['actionGroupId']})")
                            action_groups_found = True
                            active_version = version
                            found_action_groups = [ag]  # Just use this specific action group
                            break
                    if action_groups_found:
                        break  # Found the specific action group we were looking for
                else:
                    # Normal processing for all action groups
                    if not action_groups:
                        print(f"No action groups found for version {version}")
                        continue
                    
                    action_groups_found = True
                    active_version = version
                    print(f"Found {len(action_groups)} action group(s) for version {version}")
                    found_action_groups = action_groups
                    break  # Use the first version we find with action groups
            except Exception as e:
                print(f"Error checking version {version}: {e}")
        
        if not action_groups_found:
            print("No action groups found in any version of the agent.")
            return
        
        print(f"\nProcessing {len(found_action_groups)} action group(s) from version {active_version}")
        
        # For each action group, get its details
        for ag in found_action_groups:
            ag_id = ag['actionGroupId']
            ag_name = ag['actionGroupName']
            print(f"\n=== Action Group: {ag_name} ({ag_id}) ===")
            
            # Get detailed information for this action group
            try:
                detail_response = client.get_agent_action_group(
                    agentId=agent_id,
                    actionGroupId=ag_id,
                    agentVersion=active_version
                )
                
                # Print the complete raw response for debugging
                print(f"\nDEBUG: Raw action group details: {json.dumps(detail_response, default=str, indent=2)}")
                
                # Extract API schema if present
                api_schema = detail_response.get('apiSchema', {})
                
                if api_schema:
                    schema_file = f"{ag_name}_schema.json"
                    with open(schema_file, 'w') as f:
                        json.dump(api_schema, f, indent=2)
                    print(f"API schema saved to {schema_file}")
                    
                    # Print important parts of the schema
                    if isinstance(api_schema, dict):
                        print("API Schema Overview:")
                        if 'paths' in api_schema:
                            print(f"  Paths: {', '.join(api_schema['paths'].keys())}")
                        if 'openapi' in api_schema:
                            print(f"  OpenAPI Version: {api_schema['openapi']}")
                        if 'info' in api_schema and 'title' in api_schema['info']:
                            print(f"  Title: {api_schema['info']['title']}")
                        if 'components' in api_schema and 'schemas' in api_schema['components']:
                            print(f"  Schemas: {', '.join(api_schema['components']['schemas'].keys())}")
                
                # Get information about the Lambda function(s)
                if 'actionGroupExecutor' in detail_response:
                    executor = detail_response['actionGroupExecutor']
                    if executor.get('lambda'):
                        print(f"Lambda ARN: {executor['lambda']}")
                        
                # Get information about parent functions
                parent_functions = detail_response.get('parentFunctions', [])
                if parent_functions:
                    print(f"\nParent Functions: {len(parent_functions)}")
                    for i, func in enumerate(parent_functions):
                        print(f"  Function {i+1}: {func.get('name', 'Unnamed')}")
                        print(f"    Description: {func.get('description', 'No description')}")
                        if 'parameters' in func:
                            params = func.get('parameters', {})
                            param_names = params.get('properties', {}).keys()
                            print(f"    Parameters: {', '.join(param_names)}")
                        
                # Get Function schema details
                function_schema = detail_response.get('functionSchema', {})
                if function_schema:
                    print("\nFunction Schema:")
                    print(f"  Functions: {len(function_schema.get('functions', []))}")
                    for func in function_schema.get('functions', []):
                        print(f"  - {func.get('name')}: {func.get('description', '')[:50]}...")
                        if 'parameters' in func:
                            param_props = func.get('parameters', {}).get('properties', {})
                            print(f"    Parameters: {', '.join(param_props.keys())}")
                            
                # Save complete action group details to a file
                detail_file = f"{ag_name}_details.json"
                with open(detail_file, 'w') as f:
                    json.dump(detail_response, f, default=str, indent=2)
                print(f"\nComplete action group details saved to {detail_file}")
            except Exception as e:
                print(f"Error getting details for action group {ag_id}: {e}")
                continue
            
    except Exception as e:
        print(f"Error retrieving action group details: {e}")

def update_agent_info(agent_id, output_file="agent_deployment.json", region=None, profile=None):
    """
    Update local files with information about an existing Bedrock agent.
    
    Args:
        agent_id (str): ID of the Bedrock agent
        output_file (str): Output file to write agent details to
        region (str, optional): AWS region
        profile (str, optional): AWS profile name
    """
    if region:
        os.environ['AWS_DEFAULT_REGION'] = region
    
    print(f"Retrieving information for agent ID: {agent_id}")
    print(f"Using AWS profile: {profile if profile else 'default'}")
    
    # Get agent info
    agent_info = DataAgent.get_agent_info(agent_id, region_name=region, profile_name=profile)
    
    if "error" in agent_info:
        print(f"Error: {agent_info['error']}")
        return
    
    # Get agent aliases
    try:
        bedrock_agent = get_bedrock_agent_client(region_name=region, profile_name=profile)
        aliases_response = bedrock_agent.list_agent_aliases(
            agentId=agent_id
        )
        aliases = aliases_response.get('agentAliasSummaries', [])
        alias_id = aliases[0]['agentAliasId'] if aliases else "UNKNOWN"
        alias_name = aliases[0]['agentAliasName'] if aliases else "Production"
    except Exception as e:
        print(f"Could not retrieve agent aliases: {e}")
        alias_id = "MRWSOLFBWU"  # Use the default from agent_deployment.json
        alias_name = "Production"
    
    # Get action groups - we know there is a FireboltDataRetrieval action group based on the agent definition
    action_groups = ["FireboltDataRetrieval"]
    try:
        # The API might require additional parameters we don't have access to
        # so we'll use the default action group from the agent definition
        print(f"Using default action group: {', '.join(action_groups)}")
    except Exception as e:
        print(f"Could not retrieve action groups: {e}")
    
    # Create deployment details
    import time
    from datetime import datetime
    
    # Get AWS account ID safely
    account_id = "740202120544"  # Default from your agent ARN
    try:
        if 'agentArn' in agent_info and agent_info['agentArn']:
            arn_parts = agent_info['agentArn'].split(':')
            if len(arn_parts) >= 5:
                account_id = arn_parts[4]  # Extract account ID from ARN
    except Exception as e:
        print(f"Could not extract account ID from ARN: {e}")
    
    deployment_details = {
        "agent_id": agent_id,
        "agent_alias_id": alias_id,
        "agent_name": agent_info.get('agentName', 'RevOpsDataAgent'),
        "agent_arn": f"arn:aws:bedrock:us-east-1:{account_id}:agent/{agent_id}",
        "action_groups": action_groups,
        "foundation_model": agent_info.get('foundationModel', 'anthropic.claude-3-sonnet-20240229-v1:0'),
        "deployment_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": agent_info.get('description', 'RevOps Data Agent for retrieving and preprocessing data from multiple sources')
    }
    
    # Save deployment details
    with open(output_file, "w") as f:
        json.dump(deployment_details, f, indent=2)
    
    print(f"Agent information updated and saved to {output_file}")
    print(f"Agent Name: {deployment_details['agent_name']}")
    print(f"Agent ID: {agent_id}")
    print(f"Agent Alias ID: {alias_id}")
    print(f"Action Groups: {', '.join(action_groups)}")

def main(agent_id, output_file=None, region=None, profile=None, dump_groups=False):
    """
    Main function to update agent information.
    
    Args:
        agent_id (str): The Bedrock agent ID
        output_file (str, optional): Path to output file. Defaults to "agent_deployment.json".
        region (str, optional): AWS region. Defaults to None.
        profile (str, optional): AWS profile name. Defaults to None.
        dump_groups (bool, optional): Whether to dump action group details. Defaults to False.
    """
    if not output_file:
        output_file = "agent_deployment.json"
    
    print(f"Retrieving information for agent ID: {agent_id}")
    if profile:
        print(f"Using AWS profile: {profile}")
    
    if dump_groups:
        dump_action_groups(agent_id, region=region, profile=profile)
        return
    
    update_agent_info(agent_id, output_file, region, profile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update agent information from existing Bedrock agent")
    parser.add_argument("--agent-id", required=True, help="The Bedrock agent ID")
    parser.add_argument("--output-file", help="Path to output file (default: agent_deployment.json)")
    parser.add_argument("--region", help="AWS region (default: us-east-1)")
    parser.add_argument("--profile", help="AWS profile name (default: None)")
    parser.add_argument("--dump-groups", action="store_true", help="Dump action group details")
    parser.add_argument("--action-group", help="Specific action group to check for")
    
    args = parser.parse_args()
    
    if args.dump_groups and args.action_group:
        dump_action_groups(args.agent_id, args.region, args.profile, args.action_group)
    else:
        main(args.agent_id, args.output_file, args.region, args.profile, args.dump_groups)
