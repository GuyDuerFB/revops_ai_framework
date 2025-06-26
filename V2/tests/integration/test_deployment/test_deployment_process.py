"""
Integration tests for the deployment process of RevOps AI Framework V2.

These tests validate the deployment script functionality and AWS resource
provisioning without making actual changes to AWS infrastructure.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from deployment.deploy import (
    DeploymentManager,
    load_config,
    validate_config,
    create_lambda_functions,
    setup_bedrock_agents,
    create_knowledge_base,
    update_deployment_state
)

class TestDeploymentProcess:
    """Tests for the deployment process of the RevOps AI Framework V2."""
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Setup mock AWS clients for testing deployment."""
        with patch('boto3.client') as mock_boto_client:
            # Create individual mock clients
            mock_lambda = MagicMock()
            mock_bedrock = MagicMock()
            mock_bedrock_agent = MagicMock()
            mock_s3 = MagicMock()
            mock_iam = MagicMock()
            mock_secretsmanager = MagicMock()
            
            # Configure boto3.client to return different mock clients based on service name
            def get_mock_client(service_name, **kwargs):
                if service_name == 'lambda':
                    return mock_lambda
                elif service_name == 'bedrock':
                    return mock_bedrock
                elif service_name == 'bedrock-agent':
                    return mock_bedrock_agent
                elif service_name == 's3':
                    return mock_s3
                elif service_name == 'iam':
                    return mock_iam
                elif service_name == 'secretsmanager':
                    return mock_secretsmanager
                return MagicMock()
            
            mock_boto_client.side_effect = get_mock_client
            
            yield {
                'lambda': mock_lambda,
                'bedrock': mock_bedrock,
                'bedrock-agent': mock_bedrock_agent,
                's3': mock_s3,
                'iam': mock_iam,
                'secretsmanager': mock_secretsmanager
            }
    
    @pytest.fixture
    def sample_deployment_config(self, tmp_path):
        """Create a sample deployment configuration file for testing."""
        config = {
            "environment": "test",
            "region": "us-east-1",
            "lambda_functions": {
                "query_lambda": {
                    "name": "firebolt-query-lambda-test",
                    "handler": "lambda_function.lambda_handler",
                    "runtime": "python3.9",
                    "source_dir": "tools/firebolt/query_lambda",
                    "memory": 256,
                    "timeout": 60
                },
                "writer_lambda": {
                    "name": "firebolt-writer-lambda-test",
                    "handler": "lambda_function.lambda_handler",
                    "runtime": "python3.9",
                    "source_dir": "tools/firebolt/writer_lambda",
                    "memory": 256,
                    "timeout": 60
                }
            },
            "bedrock_agents": {
                "data_agent": {
                    "name": "revops-data-agent-test",
                    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "description": "Data Analysis Agent for RevOps AI",
                    "knowledge_base_id": "KB-DATA-TEST"
                },
                "decision_agent": {
                    "name": "revops-decision-agent-test",
                    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "description": "Decision Agent for RevOps AI",
                    "knowledge_base_id": "KB-DECISION-TEST"
                },
                "execution_agent": {
                    "name": "revops-execution-agent-test",
                    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "description": "Execution Agent for RevOps AI",
                    "knowledge_base_id": "KB-EXECUTION-TEST"
                }
            },
            "knowledge_bases": {
                "data_kb": {
                    "name": "revops-data-kb-test",
                    "description": "Knowledge base for data analysis",
                    "source_bucket": "revops-kb-bucket-test",
                    "source_prefix": "data/"
                },
                "decision_kb": {
                    "name": "revops-decision-kb-test",
                    "description": "Knowledge base for decision making",
                    "source_bucket": "revops-kb-bucket-test",
                    "source_prefix": "decision/"
                }
            },
            "s3_buckets": {
                "knowledge_bucket": "revops-kb-bucket-test",
                "lambda_bucket": "revops-lambda-bucket-test"
            }
        }
        
        config_path = tmp_path / "deployment_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        return str(config_path)
    
    def test_load_config_success(self, sample_deployment_config):
        """Test successfully loading deployment configuration."""
        config = load_config(sample_deployment_config)
        
        assert config["environment"] == "test"
        assert config["region"] == "us-east-1"
        assert "lambda_functions" in config
        assert "bedrock_agents" in config
        assert "knowledge_bases" in config
        assert "s3_buckets" in config
    
    def test_load_config_file_not_found(self):
        """Test handling non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            load_config("/path/to/nonexistent/config.json")
    
    def test_validate_config_valid(self, sample_deployment_config):
        """Test validating a valid configuration file."""
        config = load_config(sample_deployment_config)
        validate_config(config)  # Should not raise exception
    
    def test_validate_config_missing_required_field(self, sample_deployment_config):
        """Test validating configuration with missing required field."""
        config = load_config(sample_deployment_config)
        # Remove required field
        del config["environment"]
        
        with pytest.raises(ValueError) as excinfo:
            validate_config(config)
        
        assert "Missing required field" in str(excinfo.value)
    
    @patch('deployment.deploy.create_lambda_package')
    def test_create_lambda_functions(self, mock_create_package, mock_aws_clients, sample_deployment_config):
        """Test creating Lambda functions during deployment."""
        # Setup mock responses
        mock_aws_clients['s3'].head_bucket.return_value = {}  # Bucket exists
        mock_aws_clients['s3'].upload_file.return_value = None
        
        mock_aws_clients['lambda'].get_function.side_effect = Exception("Function not found")  # Function doesn't exist
        mock_aws_clients['lambda'].create_function.return_value = {
            "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:test-function"
        }
        
        # Setup mock for IAM role
        mock_aws_clients['iam'].get_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::123456789012:role/test-role"
            }
        }
        
        # Mock the package creation
        mock_create_package.return_value = "/tmp/lambda_package.zip"
        
        # Load config
        config = load_config(sample_deployment_config)
        
        # Execute function
        result = create_lambda_functions(config, mock_aws_clients['lambda'], mock_aws_clients['s3'], mock_aws_clients['iam'], "test-role")
        
        # Verify Lambda functions were created
        assert len(result) == 2  # Two Lambda functions in config
        assert "firebolt-query-lambda-test" in result
        assert "firebolt-writer-lambda-test" in result
        assert mock_aws_clients['lambda'].create_function.call_count == 2
    
    def test_setup_bedrock_agents(self, mock_aws_clients, sample_deployment_config):
        """Test setting up Bedrock Agents during deployment."""
        # Mock responses for Bedrock Agent creation
        mock_aws_clients['bedrock-agent'].list_agents.return_value = {
            "agentSummaries": []  # No existing agents
        }
        
        mock_aws_clients['bedrock-agent'].create_agent.return_value = {
            "agent": {
                "agentId": "test-agent-id",
                "agentName": "test-agent-name"
            }
        }
        
        mock_aws_clients['bedrock-agent'].create_agent_alias.return_value = {
            "agentAlias": {
                "agentAliasId": "test-alias-id",
                "agentAliasName": "TSTALIASNAME"
            }
        }
        
        # Load config
        config = load_config(sample_deployment_config)
        
        # Execute function
        result = setup_bedrock_agents(config, mock_aws_clients['bedrock-agent'])
        
        # Verify Bedrock Agents were created
        assert len(result) == 3  # Three agents in config
        assert "data_agent" in result
        assert "decision_agent" in result
        assert "execution_agent" in result
        assert mock_aws_clients['bedrock-agent'].create_agent.call_count == 3
        assert mock_aws_clients['bedrock-agent'].create_agent_alias.call_count == 3
    
    def test_create_knowledge_base(self, mock_aws_clients, sample_deployment_config):
        """Test creating Knowledge Bases during deployment."""
        # Mock responses for Knowledge Base creation
        mock_aws_clients['bedrock-agent'].list_knowledge_bases.return_value = {
            "knowledgeBaseSummaries": []  # No existing knowledge bases
        }
        
        mock_aws_clients['bedrock-agent'].create_knowledge_base.return_value = {
            "knowledgeBase": {
                "knowledgeBaseId": "test-kb-id",
                "name": "test-kb-name"
            }
        }
        
        # Mock S3 bucket check
        mock_aws_clients['s3'].head_bucket.return_value = {}  # Bucket exists
        
        # Load config
        config = load_config(sample_deployment_config)
        
        # Execute function
        result = create_knowledge_base(config, mock_aws_clients['bedrock-agent'], mock_aws_clients['s3'])
        
        # Verify Knowledge Bases were created
        assert len(result) == 2  # Two knowledge bases in config
        assert "data_kb" in result
        assert "decision_kb" in result
        assert mock_aws_clients['bedrock-agent'].create_knowledge_base.call_count == 2
    
    @patch('builtins.open', new_callable=mock_open)
    def test_update_deployment_state(self, mock_file_open, sample_deployment_config):
        """Test updating the deployment state tracking file."""
        # Mock the deployment state data
        deployed_resources = {
            "lambda_functions": {
                "firebolt-query-lambda-test": "arn:aws:lambda:us-east-1:123456789012:function:firebolt-query-lambda-test"
            },
            "bedrock_agents": {
                "data_agent": {
                    "agent_id": "test-agent-id",
                    "agent_alias_id": "test-alias-id"
                }
            },
            "knowledge_bases": {
                "data_kb": "test-kb-id"
            }
        }
        
        # Execute function
        update_deployment_state(deployed_resources, "deployment_state.json")
        
        # Verify file was written
        mock_file_open.assert_called_once_with("deployment_state.json", 'w')
        handle = mock_file_open()
        
        # Check that the JSON data written matches our resources
        handle.write.assert_called_once()
        written_data = handle.write.call_args[0][0]
        parsed_data = json.loads(written_data)
        
        assert parsed_data == deployed_resources
    
    @patch('deployment.deploy.create_lambda_functions')
    @patch('deployment.deploy.setup_bedrock_agents')
    @patch('deployment.deploy.create_knowledge_base')
    @patch('deployment.deploy.update_deployment_state')
    def test_deployment_manager_deploy(self, mock_update_state, mock_create_kb, 
                                      mock_setup_agents, mock_create_lambda, 
                                      mock_aws_clients, sample_deployment_config):
        """Test the complete deployment process using DeploymentManager."""
        # Setup mock return values
        mock_create_lambda.return_value = {
            "firebolt-query-lambda-test": "arn:aws:lambda:us-east-1:123456789012:function:firebolt-query-lambda-test"
        }
        
        mock_setup_agents.return_value = {
            "data_agent": {
                "agent_id": "test-agent-id",
                "agent_alias_id": "test-alias-id"
            }
        }
        
        mock_create_kb.return_value = {
            "data_kb": "test-kb-id"
        }
        
        # Load config
        config = load_config(sample_deployment_config)
        
        # Create deployment manager and deploy
        deployment_manager = DeploymentManager(config_path=sample_deployment_config)
        deployment_manager.deploy(dry_run=True)  # Use dry_run to prevent actual AWS calls
        
        # Verify each step was called
        mock_create_lambda.assert_called_once()
        mock_setup_agents.assert_called_once()
        mock_create_kb.assert_called_once()
        mock_update_state.assert_called_once()
    
    @patch('deployment.deploy.create_lambda_functions')
    def test_deployment_manager_error_handling(self, mock_create_lambda, 
                                             mock_aws_clients, sample_deployment_config):
        """Test error handling during deployment process."""
        # Setup mock to raise exception
        mock_create_lambda.side_effect = Exception("Lambda creation failed")
        
        # Create deployment manager and deploy
        deployment_manager = DeploymentManager(config_path=sample_deployment_config)
        
        # Verify exception is caught and reported
        with pytest.raises(Exception) as excinfo:
            deployment_manager.deploy(dry_run=True)
        
        assert "Deployment failed" in str(excinfo.value)
        assert "Lambda creation failed" in str(excinfo.value)
