"""
RevOps AI Framework V2 - Configuration Loader Utility

Loads and processes configuration from multiple sources:
- Default configuration template
- Environment variables
- AWS Parameter Store (optional)
- Configuration file
"""

import json
import os
import re
import logging
import boto3
from typing import Dict, Any, Optional, Union, List

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

# Default configuration template
DEFAULT_CONFIG = {
    "features": {
        "queue_processing": {
            "enabled": False,
            "queue_url": None,
            "retries": {
                "max_attempts": 3,
                "backoff_base": 2
            }
        },
        "bedrock_agent_compatibility": {
            "enabled": False,
            "response_format": "agent_function"
        },
        "payload_enrichment": {
            "enabled": True,
            "add_timestamp": True,
            "add_request_id": True,
            "add_context": True
        },
        "metrics": {
            "enabled": False,
            "namespace": "WebhookLambda"
        }
    },
    "webhooks": {
        "path": None,
        "allow_direct_url": True,
        "url_secret_name": None
    },
    "logging": {
        "level": "INFO"
    }
}

class ConfigLoader:
    """
    Configuration loader that resolves configuration from multiple sources
    with variable interpolation.
    """
    
    def __init__(self):
        """Initialize the configuration loader with default settings."""
        self.config = DEFAULT_CONFIG
    
    def _resolve_env_vars(self, value: str) -> str:
        """
        Resolve environment variable references in string values.
        
        Format: ${env:VARIABLE_NAME} or ${env:VARIABLE_NAME:default_value}
        
        Args:
            value: String value that may contain environment variable references
            
        Returns:
            String with resolved environment variables
        """
        if not isinstance(value, str):
            return value
            
        # Match ${env:VAR_NAME} or ${env:VAR_NAME:default}
        pattern = r'\${env:([^:}]+)(?::([^}]+))?}'
        
        def replace_var(match):
            var_name = match.group(1)
            default = match.group(2) if match.group(2) else None
            return os.environ.get(var_name, default if default is not None else '')
            
        return re.sub(pattern, replace_var, value)
    
    def _resolve_references(self, config_obj: Any) -> Any:
        """
        Recursively resolve variable references in configuration object.
        
        Args:
            config_obj: Configuration object (dict, list, or scalar)
            
        Returns:
            Configuration with resolved variables
        """
        if isinstance(config_obj, dict):
            return {k: self._resolve_references(v) for k, v in config_obj.items()}
        elif isinstance(config_obj, list):
            return [self._resolve_references(item) for item in config_obj]
        elif isinstance(config_obj, str):
            return self._resolve_env_vars(config_obj)
        else:
            return config_obj
    
    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            Configuration dictionary or empty dict if file not found
        """
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file: {str(e)}")
            return {}
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries.
        
        Args:
            base: Base configuration
            override: Override configuration (takes precedence)
            
        Returns:
            Merged configuration
        """
        result = base.copy()
        
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_config(result[key], value)
            else:
                # Override or add value
                result[key] = value
                
        return result
    
    def _configure_from_env(self) -> Dict[str, Any]:
        """
        Configure from environment variables using predefined mappings.
        
        Returns:
            Configuration from environment variables
        """
        env_config = {}
        
        # Queue processing
        if os.environ.get('WEBHOOK_QUEUE_URL'):
            env_config.setdefault('features', {}).setdefault('queue_processing', {})
            env_config['features']['queue_processing']['enabled'] = True
            env_config['features']['queue_processing']['queue_url'] = os.environ.get('WEBHOOK_QUEUE_URL')
        
        # Retry configuration
        if os.environ.get('WEBHOOK_RETRIES_ENABLED'):
            env_config.setdefault('features', {}).setdefault('queue_processing', {}).setdefault('retries', {})
            env_config['features']['queue_processing']['retries']['enabled'] = os.environ.get('WEBHOOK_RETRIES_ENABLED').lower() == 'true'
            
        if os.environ.get('WEBHOOK_MAX_RETRIES'):
            env_config.setdefault('features', {}).setdefault('queue_processing', {}).setdefault('retries', {})
            try:
                env_config['features']['queue_processing']['retries']['max_attempts'] = int(os.environ.get('WEBHOOK_MAX_RETRIES'))
            except ValueError:
                pass
        
        # Bedrock compatibility
        if os.environ.get('WEBHOOK_ENABLE_BEDROCK'):
            env_config.setdefault('features', {}).setdefault('bedrock_agent_compatibility', {})
            env_config['features']['bedrock_agent_compatibility']['enabled'] = os.environ.get('WEBHOOK_ENABLE_BEDROCK').lower() == 'true'
        
        # Webhook configuration
        if os.environ.get('WEBHOOK_CONFIG_PATH'):
            env_config.setdefault('webhooks', {})
            env_config['webhooks']['path'] = os.environ.get('WEBHOOK_CONFIG_PATH')
            
        if os.environ.get('WEBHOOK_URL_SECRET'):
            env_config.setdefault('webhooks', {})
            env_config['webhooks']['url_secret_name'] = os.environ.get('WEBHOOK_URL_SECRET')
            
        # Logging configuration
        if os.environ.get('LOG_LEVEL'):
            env_config.setdefault('logging', {})
            env_config['logging']['level'] = os.environ.get('LOG_LEVEL')
            
        return env_config
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from all sources and resolve variables.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            Resolved configuration dictionary
        """
        # Start with default configuration
        merged_config = self.config.copy()
        
        # Load from environment variables
        env_config = self._configure_from_env()
        merged_config = self._merge_config(merged_config, env_config)
        
        # Load from file if specified
        if config_path:
            file_config = self._load_from_file(config_path)
            merged_config = self._merge_config(merged_config, file_config)
            
        # Resolve variable references
        resolved_config = self._resolve_references(merged_config)
        
        return resolved_config

# Helper function for easier access
def load_configuration(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from all sources.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Resolved configuration dictionary
    """
    loader = ConfigLoader()
    return loader.load_config(config_path)
