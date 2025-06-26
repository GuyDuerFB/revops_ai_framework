"""
RevOps AI Framework V2 - Test Configuration

This module contains fixtures and configuration for testing the framework.
"""

import os
import json
import pytest
import boto3
from unittest.mock import MagicMock
# Import moto for AWS service mocking
import moto

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def s3_client(aws_credentials):
    with moto.mock_aws():
        conn = boto3.client("s3", region_name="us-east-1")
        yield conn

@pytest.fixture
def lambda_client(aws_credentials):
    with moto.mock_aws():
        conn = boto3.client("lambda", region_name="us-east-1")
        yield conn

@pytest.fixture
def secretsmanager_client(aws_credentials):
    with moto.mock_aws():
        conn = boto3.client("secretsmanager", region_name="us-east-1")
        yield conn

@pytest.fixture
def mock_bedrock_client(monkeypatch):
    """Mock the Bedrock client for testing."""
    mock_client = MagicMock()
    
    # Mock the invoke_agent method
    mock_invoke = MagicMock()
    mock_invoke.return_value = {
        "completion": "This is a mock response from Bedrock",
        "stopReason": "COMPLETE"
    }
    mock_client.invoke_agent = mock_invoke
    
    monkeypatch.setattr(
        "boto3.client", 
        lambda service, region_name=None: mock_client if service in ['bedrock', 'bedrock-agent', 'bedrock-agent-runtime'] else boto3.client(service, region_name=region_name)
    )
    
    return mock_client

@pytest.fixture
def sample_firebolt_credentials():
    """Create sample Firebolt credentials for testing."""
    return {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret"
    }

@pytest.fixture
def setup_secrets(secretsmanager_client, sample_firebolt_credentials):
    """Set up secrets in mock secretsmanager."""
    secretsmanager_client.create_secret(
        Name="firebolt-credentials",
        SecretString=json.dumps(sample_firebolt_credentials)
    )
    return secretsmanager_client

@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return {
        "project_name": "revops-ai-test",
        "region_name": "us-east-1",
        "profile_name": None,
        "data_agent": {
            "agent_id": "test-data-agent-id",
            "agent_alias_id": "test-data-agent-alias-id",
            "foundation_model": "anthropic.claude-3-sonnet-20240229-v1:0"
        },
        "decision_agent": {
            "agent_id": "test-decision-agent-id", 
            "agent_alias_id": "test-decision-agent-alias-id",
            "foundation_model": "anthropic.claude-3-sonnet-20240229-v1:0"
        },
        "execution_agent": {
            "agent_id": "test-execution-agent-id",
            "agent_alias_id": "test-execution-agent-alias-id",
            "foundation_model": "anthropic.claude-3-sonnet-20240229-v1:0"
        },
        "firebolt": {
            "account_name": "test-account",
            "engine_name": "test-engine",
            "credentials_secret": "firebolt-credentials"
        }
    }

@pytest.fixture
def mock_firebolt_api(requests_mock):
    """Mock the Firebolt API for testing."""
    # Mock the OAuth token endpoint
    requests_mock.post(
        "https://id.app.firebolt.io/oauth/token",
        json={"access_token": "mock-token", "expires_in": 3600}
    )
    
    # Mock the query endpoint
    requests_mock.post(
        "https://api.app.firebolt.io/query/test-account/test-engine",
        json={
            "data": {
                "metadata": [
                    {"name": "column1", "type": "STRING"},
                    {"name": "column2", "type": "INTEGER"}
                ],
                "rows": [
                    ["value1", 100],
                    ["value2", 200]
                ]
            }
        }
    )
    
    return requests_mock
