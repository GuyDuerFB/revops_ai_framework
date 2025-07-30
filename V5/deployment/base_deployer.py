#!/usr/bin/env python3
"""
Base Deployment Class for RevOps AI Framework
==============================================

Common deployment functionality shared across all deployment scripts.
Eliminates code duplication by providing base deployment patterns.
"""

import boto3
import json
import logging
import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class BaseDeployer(ABC):
    """Base class for all RevOps AI Framework deployers"""
    
    def __init__(self, config_file="config.json"):
        """Initialize the base deployer"""
        self.config_file = config_file
        self.config = self.load_config()
        
        # Initialize AWS clients
        profile_name = self.config.get('profile_name', 'FireboltSystemAdministrator-740202120544')
        region_name = self.config.get('region_name', 'us-east-1')
        
        session = boto3.Session(profile_name=profile_name)
        self.bedrock_client = session.client('bedrock-agent', region_name=region_name)
        self.bedrock_runtime_client = session.client('bedrock', region_name=region_name)
        self.lambda_client = session.client('lambda', region_name=region_name)
        self.iam_client = session.client('iam', region_name=region_name)
        
        self.region_name = region_name
        self.profile_name = profile_name
        
        logger.info(f"{self.__class__.__name__} initialized - Profile: {profile_name}, Region: {region_name}")
    
    def load_config(self):
        """Load deployment configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file: {e}")
            return {}
    
    def create_lambda_package(self, source_dir, output_zip, exclude_patterns=None):
        """Create Lambda deployment package"""
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '*.pyc', '.DS_Store', 'test_*.py', '*.log']
        
        logger.info(f"Creating Lambda package from {source_dir}")
        
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Remove excluded directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                
                for file in files:
                    # Skip excluded files
                    if any(pattern in file for pattern in exclude_patterns):
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Lambda package created: {output_zip}")
        return output_zip
    
    def update_lambda_function(self, function_name, zip_file_path):
        """Update Lambda function code"""
        try:
            with open(zip_file_path, 'rb') as zip_file:
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_file.read()
                )
            
            logger.info(f"Lambda function {function_name} updated successfully")
            return response
        except Exception as e:
            logger.error(f"Failed to update Lambda function {function_name}: {e}")
            raise
    
    def create_bedrock_agent(self, agent_config):
        """Create Bedrock agent with configuration"""
        try:
            response = self.bedrock_client.create_agent(**agent_config)
            logger.info(f"Bedrock agent created: {response['agent']['agentId']}")
            return response
        except Exception as e:
            logger.error(f"Failed to create Bedrock agent: {e}")
            raise
    
    def update_bedrock_agent(self, agent_id, agent_config):
        """Update existing Bedrock agent"""
        try:
            response = self.bedrock_client.update_agent(
                agentId=agent_id,
                **agent_config
            )
            logger.info(f"Bedrock agent {agent_id} updated successfully")
            return response
        except Exception as e:
            logger.error(f"Failed to update Bedrock agent {agent_id}: {e}")
            raise
    
    def prepare_agent(self, agent_id):
        """Prepare Bedrock agent for use"""
        try:
            response = self.bedrock_client.prepare_agent(agentId=agent_id)
            logger.info(f"Bedrock agent {agent_id} prepared successfully")
            return response
        except Exception as e:
            logger.error(f"Failed to prepare Bedrock agent {agent_id}: {e}")
            raise
    
    def create_agent_alias(self, agent_id, alias_name, description="Production alias"):
        """Create agent alias"""
        try:
            response = self.bedrock_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName=alias_name,
                description=description
            )
            logger.info(f"Agent alias {alias_name} created for agent {agent_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to create agent alias: {e}")
            raise
    
    def cleanup_temp_files(self, file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {e}")
    
    def validate_deployment(self):
        """Validate deployment prerequisites"""
        required_config = self.get_required_config()
        
        for key in required_config:
            if key not in self.config:
                logger.error(f"Missing required configuration: {key}")
                return False
        
        return True
    
    @abstractmethod
    def get_required_config(self):
        """Return list of required configuration keys"""
        pass
    
    @abstractmethod
    def deploy(self):
        """Execute the deployment"""
        pass
    
    def run_deployment(self):
        """Main deployment entry point"""
        logger.info(f"Starting {self.__class__.__name__} deployment...")
        
        if not self.validate_deployment():
            logger.error("Deployment validation failed")
            return False
        
        try:
            result = self.deploy()
            logger.info("Deployment completed successfully")
            return result
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False