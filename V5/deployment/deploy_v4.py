#!/usr/bin/env python3
"""
RevOps AI Framework V4 - Production Deployment
==============================================

Deployment script for the V4 architecture with Manager Agent and Deal Analysis Agent.
"""

from base_deployer import BaseDeployer
import logging

logger = logging.getLogger(__name__)

class V4Deployer(BaseDeployer):
    """V4 Architecture Deployment Manager"""
    
    def get_required_config(self):
        """Return list of required configuration keys"""
        return [
            'manager_agent_name',
            'deal_analysis_agent_name',
            'lambda_functions',
            'bedrock_model_arn'
        ]
    
    def deploy(self):
        """Execute V4 deployment"""
        logger.info("Deploying V4 architecture...")
        
        # Deploy Lambda functions
        lambda_functions = self.config.get('lambda_functions', {})
        for func_name, func_config in lambda_functions.items():
            self._deploy_lambda_function(func_name, func_config)
        
        # Deploy Bedrock agents
        self._deploy_manager_agent()
        self._deploy_deal_analysis_agent()
        
        logger.info("V4 deployment completed")
        return True
    
    def _deploy_lambda_function(self, func_name, func_config):
        """Deploy individual Lambda function"""
        source_dir = func_config.get('source_dir')
        if not source_dir:
            logger.error(f"No source directory specified for {func_name}")
            return
        
        # Create deployment package
        zip_path = f"/tmp/{func_name}_deployment.zip"
        self.create_lambda_package(source_dir, zip_path)
        
        # Update function
        self.update_lambda_function(func_name, zip_path)
        
        # Clean up
        self.cleanup_temp_files([zip_path])
    
    def _deploy_manager_agent(self):
        """Deploy Manager Agent"""
        agent_config = {
            'agentName': self.config['manager_agent_name'],
            'description': 'RevOps AI Framework V4 Manager Agent',
            'foundationModel': self.config['bedrock_model_arn'],
            'instruction': self._get_manager_instructions()
        }
        
        agent_id = self.config.get('manager_agent_id')
        if agent_id:
            self.update_bedrock_agent(agent_id, agent_config)
        else:
            response = self.create_bedrock_agent(agent_config)
            agent_id = response['agent']['agentId']
        
        self.prepare_agent(agent_id)
        return agent_id
    
    def _deploy_deal_analysis_agent(self):
        """Deploy Deal Analysis Agent"""
        agent_config = {
            'agentName': self.config['deal_analysis_agent_name'],
            'description': 'RevOps AI Framework V4 Deal Analysis Agent',
            'foundationModel': self.config['bedrock_model_arn'],
            'instruction': self._get_deal_analysis_instructions()
        }
        
        agent_id = self.config.get('deal_analysis_agent_id')
        if agent_id:
            self.update_bedrock_agent(agent_id, agent_config)
        else:
            response = self.create_bedrock_agent(agent_config)
            agent_id = response['agent']['agentId']
        
        self.prepare_agent(agent_id)
        return agent_id
    
    def _get_manager_instructions(self):
        """Get Manager Agent instructions"""
        return '''
# Manager Agent Instructions - RevOps AI Framework V4

## Agent Purpose
You are the Manager Agent for Firebolt's RevOps AI Framework V4. 
You serve as the intelligent router and coordinator for revenue operations analysis.

## Your Responsibilities
1. Analyze user queries to determine the best approach
2. Route specialized requests to dedicated agents
3. Handle general requests using your full capabilities
4. Ensure consistent formatting across all responses
'''
    
    def _get_deal_analysis_instructions(self):
        """Get Deal Analysis Agent instructions"""
        return '''
# Deal Analysis Agent Instructions - RevOps AI Framework V4

## Agent Purpose
You are the Deal Analysis Agent specialized in comprehensive deal evaluation and insights.

## Your Responsibilities
1. Analyze deal data and provide insights
2. Assess deal health and progression
3. Identify risks and opportunities
4. Provide actionable recommendations
'''

if __name__ == "__main__":
    deployer = V4Deployer()
    success = deployer.run_deployment()
    exit(0 if success else 1)