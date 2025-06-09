#!/usr/bin/env python3
"""
Configuration module for AWS services.
Contains settings and credential handling for AWS operations.
"""
import os
import configparser
from pathlib import Path

def load_aws_credentials(profile_name='default'):
    """
    Load AWS credentials from a config file or environment variables.
    
    Args:
        profile_name (str): AWS profile name to use
    
    Returns:
        dict: Dictionary containing AWS credentials
    """
    # Path to credentials file within the project
    credentials_file = Path(__file__).parent.parent / 'credentials.ini'
    
    # If credentials file exists, read from there
    if credentials_file.exists():
        config = configparser.ConfigParser()
        config.read(credentials_file)
        
        if profile_name in config:
            credentials = {
                'aws_access_key_id': config[profile_name].get('aws_access_key_id'),
                'aws_secret_access_key': config[profile_name].get('aws_secret_access_key'),
                'region_name': config[profile_name].get('region_name', 'us-west-2')
            }
            
            # Add session token if present (for temporary credentials)
            session_token = config[profile_name].get('aws_session_token')
            if session_token:
                credentials['aws_session_token'] = session_token
                
            return credentials
    
    # Otherwise, try environment variables
    credentials = {
        'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'region_name': os.environ.get('AWS_DEFAULT_REGION', 'us-west-2')
    }
    
    # Add session token from environment if present
    session_token = os.environ.get('AWS_SESSION_TOKEN')
    if session_token:
        credentials['aws_session_token'] = session_token
        
    return credentials
