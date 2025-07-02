# RevOps AI Framework - Simplified Deployment

This directory contains the simplified, streamlined deployment process for the RevOps AI Framework. It's designed to be straightforward and easy to use for both humans and AI agents.

## Directory Structure

```
/deployment_simplified/
├── README.md               # This file
├── deploy.py               # Main deployment script
├── config.json             # Current deployment configuration
├── requirements.txt        # Python dependencies for deployment
├── scripts/
│   └── aws_cli_agent_manager.py  # AWS CLI wrapper for agent management
```

## Quick Start

1. **Environment Setup**
   ```bash
   # Create and activate Python virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   
   # Install required packages
   pip install -r requirements.txt
   ```

2. **Deploy Components**
   ```bash
   # Deploy all components (Lambda functions, knowledge base, agents)
   python deploy.py --deploy
   
   # Deploy specific components
   python deploy.py --deploy lambda kb data_agent decision_agent
   
   # Deploy and test in one command
   python deploy.py --deploy lambda --test lambda
   ```

3. **AWS CLI Agent Management**
   If you encounter issues with agent deployment, use the AWS CLI wrapper:
   ```bash
   # List all AWS Bedrock agents
   python scripts/aws_cli_agent_manager.py list-agents
   
   # Get details about a specific agent
   python scripts/aws_cli_agent_manager.py get-agent YOUR_AGENT_ID
   
   # List agent aliases
   python scripts/aws_cli_agent_manager.py list-aliases YOUR_AGENT_ID
   
   # Create an agent alias
   python scripts/aws_cli_agent_manager.py create-alias YOUR_AGENT_ID ALIAS_NAME
   
   # Update config.json with agent/alias IDs
   python scripts/aws_cli_agent_manager.py update-config data_agent YOUR_AGENT_ID YOUR_ALIAS_ID
   ```

## Key Deployment Notes

1. **AWS Credentials**
   - Ensure AWS CLI is configured with profile `FireboltSystemAdministrator-740202120544`
   - Region should be set to `us-east-1`

2. **Agent ID Management**
   - If deploying to existing agents, update `config.json` with the correct agent_id before deployment
   - Use `aws_cli_agent_manager.py` to manage agent IDs and aliases when needed

3. **Common Issues**
   - If Lambda deployment fails with ResourceConflictException, wait a few minutes and try again
   - If agent is in "Not Prepared" state, use AWS console or CLI to check status and prepare if needed

## Deployment Workflow

1. Deploy Lambda functions
2. Deploy knowledge base
3. Deploy agents (data_agent, decision_agent, execution_agent)
4. Test each component after deployment

For detailed AWS Bedrock documentation, refer to the [AWS Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
