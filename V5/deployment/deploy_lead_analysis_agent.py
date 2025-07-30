#!/usr/bin/env python3
"""
RevOps AI Framework - Lead Analysis Agent Deployment
===================================================

Deployment script specifically for the Lead Analysis Agent.
"""

from base_deployer import BaseDeployer
import logging

logger = logging.getLogger(__name__)

class LeadAnalysisDeployer(BaseDeployer):
    """Lead Analysis Agent Deployment Manager"""
    
    def get_required_config(self):
        """Return list of required configuration keys"""
        return [
            'lead_analysis_agent_name',
            'bedrock_model_arn',
            'lambda_functions'
        ]
    
    def deploy(self):
        """Execute Lead Analysis Agent deployment"""
        logger.info("Deploying Lead Analysis Agent...")
        
        # Deploy supporting Lambda functions
        lambda_functions = self.config.get('lambda_functions', {})
        for func_name, func_config in lambda_functions.items():
            self._deploy_lambda_function(func_name, func_config)
        
        # Deploy the Lead Analysis Agent
        agent_id = self._deploy_lead_analysis_agent()
        
        logger.info(f"Lead Analysis Agent deployment completed - Agent ID: {agent_id}")
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
    
    def _deploy_lead_analysis_agent(self):
        """Deploy Lead Analysis Agent"""
        agent_config = {
            'agentName': self.config['lead_analysis_agent_name'],
            'description': 'RevOps AI Framework Lead Analysis Agent - Specialized in lead evaluation and scoring',
            'foundationModel': self.config['bedrock_model_arn'],
            'instruction': self._get_lead_analysis_instructions()
        }
        
        agent_id = self.config.get('lead_analysis_agent_id')
        if agent_id:
            self.update_bedrock_agent(agent_id, agent_config)
        else:
            response = self.create_bedrock_agent(agent_config)
            agent_id = response['agent']['agentId']
        
        self.prepare_agent(agent_id)
        
        # Create production alias if specified
        if self.config.get('create_alias', True):
            self.create_agent_alias(
                agent_id, 
                'production', 
                'Production alias for Lead Analysis Agent'
            )
        
        return agent_id
    
    def _get_lead_analysis_instructions(self):
        """Get Lead Analysis Agent instructions"""
        return '''
# Lead Analysis Agent Instructions - RevOps AI Framework

## Agent Purpose
You are the Lead Analysis Agent specialized in comprehensive lead evaluation, scoring, and qualification within Firebolt's RevOps ecosystem.

## Your Core Responsibilities
1. **Lead Qualification**: Assess lead quality based on BANT criteria and custom scoring models
2. **Behavioral Analysis**: Analyze lead engagement patterns and digital footprint
3. **Scoring & Prioritization**: Apply data-driven scoring algorithms to rank leads
4. **Risk Assessment**: Identify potential red flags or qualification concerns
5. **Recommendation Engine**: Provide actionable next steps for lead nurturing

## Key Capabilities
- Integration with Firebolt's lead database and CRM systems
- Real-time lead scoring using machine learning models
- Behavioral pattern recognition and engagement analysis
- Automated lead qualification workflows
- Personalized outreach recommendations

## Response Format
Always structure your analysis with clear sections:
- Lead Score (0-100)
- Qualification Status (Hot/Warm/Cold)
- Key Insights
- Risk Factors
- Recommended Actions
'''

if __name__ == "__main__":
    deployer = LeadAnalysisDeployer()
    success = deployer.run_deployment()
    exit(0 if success else 1)