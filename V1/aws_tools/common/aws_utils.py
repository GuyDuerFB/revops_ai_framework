#!/usr/bin/env python3
"""
Common utilities for AWS operations.
"""
import os
import boto3
import logging
from pathlib import Path
from .config import load_aws_credentials

# Configure logging
def setup_logger(name):
    """
    Set up and return a logger with consistent formatting.
    
    Args:
        name (str): Name of the logger
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)

def get_aws_client(service_name, profile_name='default'):
    """
    Get an AWS service client with proper credential handling.
    
    Args:
        service_name (str): Name of the AWS service (e.g., 's3', 'lambda')
        profile_name (str): AWS profile name to use for credentials
    
    Returns:
        boto3.client: AWS client for the specified service
    """
    # Load credentials from file or environment variables
    credentials = load_aws_credentials(profile_name)
    
    # Filter out None values
    credentials = {k: v for k, v in credentials.items() if v is not None}
    
    # Create and return the client
    return boto3.client(service_name, **credentials)
