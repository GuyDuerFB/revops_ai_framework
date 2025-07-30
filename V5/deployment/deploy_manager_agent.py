#!/usr/bin/env python3
"""
RevOps AI Framework - Manager Agent Deployment
==============================================

Deployment script specifically for the Manager Agent.
"""

from base_deployer import BaseDeployer
import logging

logger = logging.getLogger(__name__)

class ManagerAgentDeployer(BaseDeployer):
    """Manager Agent Deployment Manager"""
    
    def get_required_config(self):
        """Return list of required configuration keys"""
        return [
            'manager_agent_name',
            'bedrock_model_arn',
            'lambda_functions',
            'action_groups'
        ]
    
    def deploy(self):
        """Execute Manager Agent deployment"""
        logger.info("Deploying Manager Agent...")
        
        # Deploy supporting Lambda functions
        lambda_functions = self.config.get('lambda_functions', {})
        for func_name, func_config in lambda_functions.items():
            self._deploy_lambda_function(func_name, func_config)
        
        # Deploy the Manager Agent
        agent_id = self._deploy_manager_agent()
        
        # Configure action groups
        self._configure_action_groups(agent_id)
        
        logger.info(f"Manager Agent deployment completed - Agent ID: {agent_id}")
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
            'description': 'RevOps AI Framework Manager Agent - Primary coordinator and router',
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
        
        # Create production alias if specified
        if self.config.get('create_alias', True):
            self.create_agent_alias(
                agent_id, 
                'production', 
                'Production alias for Manager Agent'
            )
        
        return agent_id
    
    def _configure_action_groups(self, agent_id):
        """Configure action groups for the Manager Agent"""
        action_groups = self.config.get('action_groups', [])
        
        for action_group in action_groups:
            try:
                response = self.bedrock_client.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    **action_group
                )
                logger.info(f"Action group {action_group['actionGroupName']} configured")
            except Exception as e:
                logger.error(f"Failed to configure action group {action_group.get('actionGroupName', 'unknown')}: {e}")
    
    def _get_manager_instructions(self):
        """Get Manager Agent instructions"""
        return '''
# Manager Agent Instructions - RevOps AI Framework

## Agent Purpose
You are the **Manager Agent** and **PRIMARY COORDINATOR** for Firebolt's RevOps AI Framework. You serve as the intelligent entry point, router, and orchestrator for all revenue operations analysis and decision-making.

## Your Role as SUPERVISOR & Router

You are the central command center for all user requests. Your responsibilities include:

1. **Intent Recognition & Analysis**: 
   - Analyze user queries to understand intent, complexity, and requirements
   - Determine the most effective approach for each request
   - Identify when specialized agents are needed vs. direct handling

2. **Intelligent Routing & Orchestration**:
   - Route deal-specific queries to the Deal Analysis Agent
   - Route lead evaluation requests to the Lead Analysis Agent  
   - Coordinate multi-agent workflows for complex requests
   - Maintain context across agent handoffs

3. **Direct Processing Capabilities**:
   - Handle general RevOps questions using your full knowledge base
   - Perform data analysis and reporting tasks
   - Execute simple queries and calculations
   - Provide strategic insights and recommendations

4. **Quality Control & Response Coordination**:
   - Ensure consistent formatting and quality across all responses
   - Synthesize multi-agent outputs into coherent final responses
   - Validate agent recommendations before delivery
   - Maintain conversation context and follow-up handling

## Key Capabilities
- Full access to Firebolt's RevOps data ecosystem
- Advanced analytics and reporting capabilities
- Integration with CRM systems and sales tools
- Real-time data processing and insights generation
- Strategic planning and forecasting support

## Response Standards
- Always acknowledge the user's request clearly
- Provide structured, actionable insights
- Use data to support all recommendations
- Maintain professional but approachable tone
- Include relevant metrics and context
'''

if __name__ == "__main__":
    deployer = ManagerAgentDeployer()
    success = deployer.run_deployment()
    exit(0 if success else 1)