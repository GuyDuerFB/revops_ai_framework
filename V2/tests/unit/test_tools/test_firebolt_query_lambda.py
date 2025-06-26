"""
Unit tests for the Firebolt Query Lambda component.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
import urllib.request
from io import BytesIO

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the module under test
from tools.firebolt.query_lambda.lambda_function import (
    extract_sql_from_markdown, 
    get_aws_secret,
    get_firebolt_credentials,
    get_firebolt_access_token,
    execute_firebolt_query,
    format_simple_result,
    query_fire,
    lambda_handler
)

class TestFireboltQueryLambda:
    """Test cases for the Firebolt Query Lambda functions."""
    
    def test_extract_sql_from_markdown_with_sql_tag(self):
        """Test extracting SQL from markdown with explicit SQL tag."""
        markdown = """
        Here's the SQL query to run:
        
        ```sql
        SELECT * FROM users
        WHERE status = 'active'
        ```
        
        This should return all active users.
        """
        
        sql = extract_sql_from_markdown(markdown)
        expected = "SELECT * FROM users\nWHERE status = 'active'"
        assert sql == expected
    
    def test_extract_sql_from_markdown_without_sql_tag(self):
        """Test extracting SQL from markdown without explicit SQL tag."""
        markdown = """
        Here's the query:
        
        ```
        SELECT * FROM orders
        WHERE order_date > '2023-01-01'
        ```
        
        This will show recent orders.
        """
        
        sql = extract_sql_from_markdown(markdown)
        expected = "SELECT * FROM orders\nWHERE order_date > '2023-01-01'"
        assert sql == expected
    
    def test_extract_sql_from_markdown_no_code_blocks(self):
        """Test extracting SQL when there are no code blocks."""
        plain_sql = "SELECT * FROM products WHERE category = 'electronics'"
        
        result = extract_sql_from_markdown(plain_sql)
        assert result == plain_sql
    
    def test_extract_sql_from_markdown_empty_input(self):
        """Test extracting SQL with empty input."""
        result = extract_sql_from_markdown("")
        assert result == ""
        
        result = extract_sql_from_markdown(None)
        assert result is None
    
    def test_get_aws_secret_success(self, secretsmanager_client, setup_secrets):
        """Test successful retrieval of secrets from AWS Secrets Manager."""
        secret_name = "firebolt-credentials"
        result = get_aws_secret(secret_name, "us-east-1")
        
        assert isinstance(result, dict)
        assert result["client_id"] == "test-client-id"
        assert result["client_secret"] == "test-client-secret"
    
    @patch('boto3.session.Session')
    def test_get_aws_secret_error(self, mock_session):
        """Test handling errors when retrieving secrets."""
        # Set up the mock to raise an exception
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = Exception("Secret not found")
        mock_session.return_value.client.return_value = mock_client
        
        with pytest.raises(Exception) as excinfo:
            get_aws_secret("nonexistent-secret", "us-east-1")
        
        assert "Failed to retrieve secret" in str(excinfo.value)
    
    def test_get_firebolt_credentials(self, secretsmanager_client, setup_secrets):
        """Test retrieving Firebolt credentials from secrets manager."""
        result = get_firebolt_credentials("firebolt-credentials", "us-east-1")
        
        assert "client_id" in result
        assert "client_secret" in result
        assert result["client_id"] == "test-client-id"
        assert result["client_secret"] == "test-client-secret"
    
    def test_get_firebolt_credentials_missing_fields(self, monkeypatch):
        """Test handling missing required fields in credentials."""
        # Mock get_aws_secret to return credentials without required fields
        def mock_get_secret(secret_name, region_name):
            return {"username": "test-user"}  # Missing client_id and client_secret
        
        monkeypatch.setattr('tools.firebolt.query_lambda.lambda_function.get_aws_secret', mock_get_secret)
        
        with pytest.raises(Exception) as excinfo:
            get_firebolt_credentials("firebolt-credentials", "us-east-1")
        
        assert "Missing required fields" in str(excinfo.value)
    
    @patch('urllib.request.urlopen')
    def test_get_firebolt_access_token_success(self, mock_urlopen):
        """Test successfully getting a Firebolt access token."""
        # Mock the response from the OAuth token endpoint
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "access_token": "test-token-123",
            "token_type": "bearer",
            "expires_in": 3600
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        credentials = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret"
        }
        
        token = get_firebolt_access_token(credentials)
        
        assert token == "test-token-123"
        
        # Verify the request was made correctly
        mock_urlopen.assert_called_once()
        request_arg = mock_urlopen.call_args[0][0]
        assert request_arg.get_full_url() == "https://id.app.firebolt.io/oauth/token"
        assert b"grant_type=client_credentials" in request_arg.data
        assert b"client_id=test-client-id" in request_arg.data
        assert b"client_secret=test-client-secret" in request_arg.data
    
    @patch('urllib.request.urlopen')
    def test_get_firebolt_access_token_missing_token(self, mock_urlopen):
        """Test handling a response with no access token."""
        # Mock the response with missing access token
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "token_type": "bearer",
            "expires_in": 3600
            # No access_token
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        credentials = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret"
        }
        
        with pytest.raises(Exception) as excinfo:
            get_firebolt_access_token(credentials)
        
        assert "No access token in response" in str(excinfo.value)
    
    @patch('tools.firebolt.query_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.query_lambda.lambda_function.get_firebolt_access_token')
    @patch('urllib.request.urlopen')
    def test_execute_firebolt_query_success(self, mock_urlopen, mock_get_token, mock_get_credentials):
        """Test successful execution of a Firebolt query."""
        # Mock dependencies
        mock_get_credentials.return_value = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret"
        }
        mock_get_token.return_value = "test-token-456"
        
        # Mock the response from the Firebolt query API
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "metadata": [
                    {"name": "user_id", "type": "INTEGER"},
                    {"name": "username", "type": "STRING"}
                ],
                "rows": [
                    [1, "john_doe"],
                    [2, "jane_smith"]
                ]
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Execute a test query
        query = "SELECT user_id, username FROM users LIMIT 10"
        result = execute_firebolt_query(
            query, 
            "firebolt-credentials", 
            "us-east-1",
            "test-account",
            "test-engine"
        )
        
        # Verify the request was made correctly
        mock_urlopen.assert_called_once()
        request_arg = mock_urlopen.call_args[0][0]
        assert request_arg.get_full_url() == "https://api.app.firebolt.io/query/test-account/test-engine"
        assert json.loads(request_arg.data.decode('utf-8')) == {"query": query}
        assert request_arg.get_header("Authorization") == "Bearer test-token-456"
        
        # Check result formatting
        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["user_id"] == 1
        assert result["results"][0]["username"] == "john_doe"
        assert result["row_count"] == 2
        assert result["column_count"] == 2
    
    def test_format_simple_result_success(self):
        """Test formatting raw query results into a simplified structure."""
        raw_result = {
            "data": {
                "metadata": [
                    {"name": "order_id", "type": "INTEGER"},
                    {"name": "order_date", "type": "DATE"},
                    {"name": "amount", "type": "FLOAT"}
                ],
                "rows": [
                    [1001, "2023-06-15", 125.99],
                    [1002, "2023-06-16", 89.50]
                ]
            }
        }
        
        result = format_simple_result(raw_result)
        
        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["order_id"] == 1001
        assert result["results"][0]["order_date"] == "2023-06-15"
        assert result["results"][0]["amount"] == 125.99
        assert result["row_count"] == 2
        assert result["column_count"] == 3
        assert [col["name"] for col in result["columns"]] == ["order_id", "order_date", "amount"]
    
    def test_format_simple_result_with_error(self):
        """Test formatting error results."""
        raw_result = {
            "error": "SQL syntax error",
            "message": "Invalid SQL statement"
        }
        
        result = format_simple_result(raw_result)
        
        assert result["success"] is False
        assert result["error"] == "SQL syntax error"
        assert result["message"] == "Invalid SQL statement"
        assert len(result["results"]) == 0
        assert len(result["columns"]) == 0
    
    def test_query_fire_success(self, monkeypatch):
        """Test the query_fire function with a successful query."""
        # Mock execute_firebolt_query
        mock_result = {
            "success": True,
            "results": [{"col1": "value1"}],
            "columns": [{"name": "col1", "type": "STRING"}],
            "row_count": 1,
            "column_count": 1
        }
        monkeypatch.setattr('tools.firebolt.query_lambda.lambda_function.execute_firebolt_query', 
                          lambda q, s, r, a, e: mock_result)
        
        # Test with a simple query
        result = query_fire("SELECT * FROM test_table")
        
        assert result == mock_result
    
    def test_query_fire_no_query(self):
        """Test query_fire with missing query parameter."""
        result = query_fire(None)
        
        assert result["success"] is False
        assert "No SQL query provided" in result["error"]
    
    def test_lambda_handler_bedrock_agent_format(self, monkeypatch):
        """Test lambda_handler with Bedrock Agent format."""
        # Mock query_fire function
        mock_result = {
            "success": True,
            "results": [{"test_col": "test_value"}]
        }
        monkeypatch.setattr('tools.firebolt.query_lambda.lambda_function.query_fire', 
                          lambda q, a=None, e=None: mock_result)
        
        # Create a mock event in Bedrock Agent format
        event = {
            "actionGroup": "firebolt_query",
            "action": "query_fire",
            "apiPath": "/query_fire",
            "body": {
                "parameters": {
                    "query": "SELECT * FROM test_table",
                    "account_name": "test-account",
                    "engine_name": "test-engine"
                }
            }
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result == mock_result
