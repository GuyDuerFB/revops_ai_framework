"""
RevOps AI Framework - Data Agent Definition

This module defines the Bedrock Agent for data retrieval operations.
The agent is schema-aware and can interact with various data sources
through Lambda function tools.

Updated to work with the existing Bedrock agent: THA3J7B4NP
"""

import json
import os
import boto3
from typing import Dict, Any, List, Optional
import time

# AWS client functions - initialized dynamically with region and profile
def get_bedrock_agent_client(region_name='us-east-1', profile_name=None):
    session = boto3.Session(region_name=region_name, profile_name=profile_name)
    return session.client('bedrock-agent')

def get_bedrock_runtime_client(region_name='us-east-1', profile_name=None):
    session = boto3.Session(region_name=region_name, profile_name=profile_name)
    return session.client('bedrock-runtime')

def get_bedrock_agent_runtime_client(region_name='us-east-1', profile_name=None):
    session = boto3.Session(region_name=region_name, profile_name=profile_name)
    return session.client('bedrock-agent-runtime')

def get_lambda_client(region_name='us-east-1', profile_name=None):
    session = boto3.Session(region_name=region_name, profile_name=profile_name)
    return session.client('lambda')

class DataAgent:
    """
    Data Agent for the RevOps AI Framework that integrates with Amazon Bedrock.
    Responsible for retrieving and preprocessing data from various sources.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_alias_id: str,
        foundation_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        """
        Initialize the Data Agent with Bedrock Agent configuration.
        
        Args:
            agent_id (str): Bedrock Agent ID
            agent_alias_id (str): Bedrock Agent Alias ID
            foundation_model (str): Foundation model to use for the agent
        """
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.foundation_model = foundation_model
    
    def invoke(self, input_text: str, session_id: Optional[str] = None, region_name: str = 'us-east-1', profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the Data Agent with a specific input prompt.
        
        Args:
            input_text (str): The prompt to send to the agent
            session_id (Optional[str]): Session ID for conversation context
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
            
        Returns:
            Dict[str, Any]: Agent response
        """
        if not session_id:
            # Generate a session ID if not provided
            from datetime import datetime
            import uuid
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            session_id = f"data_agent_{timestamp}_{unique_id}"
        
        # Get bedrock agent runtime client (for invocation)
        bedrock_agent_runtime = get_bedrock_agent_runtime_client(region_name, profile_name)
        
        try:
            # Invoke the Bedrock Agent using the agent-runtime client
            response = bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=input_text
            )
            
            # Process and return the response
            return {
                "agent_response": response,
                "session_id": session_id
            }
        except Exception as e:
            print(f"Error invoking agent: {e}")
            # If we get a specific type of error, try another method
            try:
                print("Attempting alternative invocation method...")
                response = bedrock_agent_runtime.invoke_agent(
                    agentId=self.agent_id, 
                    agentAliasId=self.agent_alias_id,
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=False
                )
                return {
                    "agent_response": response,
                    "session_id": session_id
                }
            except Exception as e2:
                return {
                    "error": f"Failed to invoke agent: {str(e2)}",
                    "session_id": session_id
                }

    
    @staticmethod
    def create_agent(
        agent_name: str,
        description: str,
        instruction_source_file: str,
        foundation_model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        action_group_definitions: Optional[List[Dict]] = None,
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Bedrock Agent with the specified configuration.
        
        Args:
            agent_name (str): Name of the agent
            description (str): Description of the agent
            instruction_source_file (str): Path to the instruction file
            foundation_model (str): Foundation model to use
            action_group_definitions (Optional[List[Dict]]): Action group definitions
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
            
        Returns:
            Dict[str, Any]: Created agent details
        """
        # Read instructions from file
        with open(instruction_source_file, 'r') as file:
            instructions = file.read()
        
        # Get bedrock agent client
        bedrock_agent_client = get_bedrock_agent_client(region_name, profile_name)
        
        # Create the agent
        response = bedrock_agent_client.create_agent(
            agentName=agent_name,
            description=description,
            instructions=instructions,
            foundationModel=foundation_model,
            actionGroupExecutor={
                'customEnabled': 'true'
            }
        )
        
        agent_id = response['agentId']
        
        # Add action groups if provided
        if action_group_definitions:
            for action_group in action_group_definitions:
                bedrock_agent_client.create_agent_action_group(
                    agentId=agent_id,
                    actionGroupName=action_group['name'],
                    description=action_group['description'],
                    apiSchema={
                        'payload': json.dumps(action_group['schema'])
                    }
                )
        
        return response
    
    @staticmethod
    def create_agent_alias(
        agent_id: str,
        alias_name: str,
        description: str = "Production alias for Data Agent",
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an alias for the Bedrock Agent.
        
        Args:
            agent_id (str): Agent ID
            alias_name (str): Name of the alias
            description (str): Description of the alias
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
            
        Returns:
            Dict[str, Any]: Created alias details
        """
        # Get bedrock agent client
        bedrock_agent_client = get_bedrock_agent_client(region_name, profile_name)
        
        response = bedrock_agent_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias_name,
            description=description
        )
        
        return response
        
    @staticmethod
    def get_agent_info(agent_id: str, region_name: str = 'us-east-1', profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about an existing Bedrock Agent.
        
        Args:
            agent_id (str): The ID of the Bedrock agent
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
            
        Returns:
            Dict[str, Any]: Agent information
        """
        try:
            # Get bedrock agent client
            bedrock_agent_client = get_bedrock_agent_client(region_name, profile_name)
            
            response = bedrock_agent_client.get_agent(
                agentId=agent_id
            )
            return response
        except Exception as e:
            print(f"Error retrieving agent information: {e}")
            return {"error": str(e)}

def prepare_action_groups() -> List[Dict[str, Any]]:
    """
    Prepare action group definitions for the Data Agent.
    
    Returns:
        List[Dict[str, Any]]: List of action group definitions
    """
    action_groups = [
        {
            "name": "FireboltDataRetrieval",
            "description": "Retrieve data from Firebolt data warehouse using SQL queries",
            "schema": {
                "openapi": "3.0.0",
                "info": {
                    "title": "Firebolt Data Retrieval API",
                    "description": "API for retrieving data from Firebolt data warehouse",
                    "version": "1.0.0"
                },
                "paths": {
                    "/execute_query": {
                        "post": {
                            "summary": "Execute a SQL query on Firebolt",
                            "description": "Execute a SQL query on the Firebolt data warehouse and return the results",
                            "operationId": "execute_firebolt_query",
                            "requestBody": {
                                "required": true,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["query"],
                                            "properties": {
                                                "query": {
                                                    "type": "string",
                                                    "description": "The SQL query to execute"
                                                },
                                                "secret_name": {
                                                    "type": "string",
                                                    "description": "Name of the AWS secret containing client_id and client_secret",
                                                    "default": "firebolt-api-credentials"
                                                },
                                                "region_name": {
                                                    "type": "string",
                                                    "description": "AWS region where the secret is stored",
                                                    "default": "eu-north-1"
                                                },
                                                "max_rows_per_chunk": {
                                                    "type": "integer",
                                                    "description": "Maximum number of rows per chunk for large results",
                                                    "default": 1000
                                                },
                                                "chunk_index": {
                                                    "type": "integer",
                                                    "description": "Which chunk to return (0 = first chunk or metadata)",
                                                    "default": 0
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful response",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {
                                                        "type": "boolean"
                                                    },
                                                    "error": {
                                                        "type": "string",
                                                        "nullable": true
                                                    },
                                                    "chunked": {
                                                        "type": "boolean"
                                                    },
                                                    "chunk_index": {
                                                        "type": "integer"
                                                    },
                                                    "total_chunks": {
                                                        "type": "integer"
                                                    },
                                                    "total_rows": {
                                                        "type": "integer"
                                                    },
                                                    "rows_per_chunk": {
                                                        "type": "integer"
                                                    },
                                                    "columns": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "string"
                                                        }
                                                    },
                                                    "results": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/get_query_chunk": {
                        "post": {
                            "summary": "Get a specific chunk of a large query result",
                            "description": "Retrieve a specific chunk from a previously executed query with large results",
                            "operationId": "get_firebolt_query_chunk",
                            "requestBody": {
                                "required": true,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["query", "chunk_index"],
                                            "properties": {
                                                "query": {
                                                    "type": "string",
                                                    "description": "The original SQL query"
                                                },
                                                "secret_name": {
                                                    "type": "string",
                                                    "description": "Name of the AWS secret containing client_id and client_secret",
                                                    "default": "firebolt-api-credentials"
                                                },
                                                "region_name": {
                                                    "type": "string",
                                                    "description": "AWS region where the secret is stored",
                                                    "default": "eu-north-1"
                                                },
                                                "chunk_index": {
                                                    "type": "integer",
                                                    "description": "Index of the chunk to retrieve (1-based)"
                                                },
                                                "max_rows_per_chunk": {
                                                    "type": "integer",
                                                    "description": "Maximum number of rows per chunk",
                                                    "default": 1000
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful response",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {
                                                        "type": "boolean"
                                                    },
                                                    "error": {
                                                        "type": "string",
                                                        "nullable": true
                                                    },
                                                    "chunked": {
                                                        "type": "boolean"
                                                    },
                                                    "chunk_index": {
                                                        "type": "integer"
                                                    },
                                                    "total_chunks": {
                                                        "type": "integer"
                                                    },
                                                    "columns": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "string"
                                                        }
                                                    },
                                                    "results": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "QueryResult": {
                            "type": "object",
                            "properties": {
                                "success": {
                                    "type": "boolean",
                                    "description": "Whether the query executed successfully"
                                },
                                "error": {
                                    "type": "string",
                                    "nullable": true,
                                    "description": "Error message if the query failed"
                                },
                                "chunked": {
                                    "type": "boolean",
                                    "description": "Whether the result is chunked due to large size"
                                },
                                "columns": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "Column names in the result set"
                                },
                                "results": {
                                    "type": "array",
                                    "items": {
                                        "type": "object"
                                    },
                                    "description": "Result rows as objects with column names as keys"
                                }
                            }
                        }
                    }
                }
            }
        }
        # Additional action groups for other data sources can be added here
        # e.g., Salesforce, Slack, Gong, etc.
    ]
    
    return action_groups
