"""
RevOps AI Framework V2 - Secret Manager Utility

Handles retrieval of secrets from AWS Secrets Manager.
Used for accessing webhook URLs and other sensitive information.
"""

import json
import boto3
import logging
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, Union

# Configure logging
logger = logging.getLogger()

class SecretManager:
    """
    Secret Manager for retrieving and caching secrets from AWS Secrets Manager.
    """
    
    def __init__(self):
        """Initialize the secret manager with an empty cache."""
        self.secrets_client = boto3.client('secretsmanager')
        self.secret_cache = {}
        
    def get_secret(self, secret_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get secret value from AWS Secrets Manager with optional caching.
        
        Args:
            secret_name: Name or ARN of the secret
            use_cache: Whether to use cached value if available
            
        Returns:
            Dictionary containing secret key-value pairs
            
        Raises:
            Exception: If secret retrieval fails
        """
        # Return from cache if enabled and available
        if use_cache and secret_name in self.secret_cache:
            return self.secret_cache[secret_name]
            
        try:
            # Get secret from AWS Secrets Manager
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            
            # Parse secret string
            if 'SecretString' in response:
                secret = json.loads(response['SecretString'])
            else:
                raise Exception("Binary secrets not supported")
                
            # Cache the secret if caching is enabled
            if use_cache:
                self.secret_cache[secret_name] = secret
                
            return secret
            
        except ClientError as e:
            logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
            raise Exception(f"Failed to retrieve secret: {str(e)}")
            
        except json.JSONDecodeError:
            logger.error(f"Error parsing secret {secret_name}: Not valid JSON")
            raise Exception("Secret is not valid JSON")
            
    def get_webhook_url(self, secret_name: str, webhook_name: Optional[str] = None) -> str:
        """
        Get webhook URL from a secret.
        
        The secret can either be a string URL or a JSON object with webhook names as keys.
        
        Args:
            secret_name: Name of the secret containing webhook URL(s)
            webhook_name: Optional webhook name if the secret contains multiple webhooks
            
        Returns:
            Webhook URL as string
            
        Raises:
            Exception: If webhook URL not found or retrieval fails
        """
        try:
            # Get the secret
            secret = self.get_secret(secret_name)
            
            # Handle string secret (direct URL)
            if isinstance(secret, str):
                return secret
                
            # Handle JSON object with webhook names
            if webhook_name:
                if webhook_name in secret:
                    return secret[webhook_name]
                else:
                    raise Exception(f"Webhook '{webhook_name}' not found in secret '{secret_name}'")
            
            # If no webhook name specified but only one URL in secret, return it
            if len(secret) == 1:
                return next(iter(secret.values()))
                
            # Default URL if available
            if "default" in secret:
                return secret["default"]
                
            raise Exception(f"No webhook URL found in secret '{secret_name}'")
            
        except Exception as e:
            logger.error(f"Error retrieving webhook URL: {str(e)}")
            raise

# Helper function for easier access
def get_secret(secret_name: str) -> Dict[str, Any]:
    """
    Get a secret from AWS Secrets Manager.
    
    Args:
        secret_name: Name or ARN of the secret
        
    Returns:
        Dictionary containing secret key-value pairs
    """
    manager = SecretManager()
    return manager.get_secret(secret_name)
