"""
Unit tests for the Firebolt Metadata Lambda component.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the module under test
from tools.firebolt.metadata_lambda.lambda_function import (
    get_firebolt_credentials,
    get_firebolt_access_token,
    fetch_schema_metadata,
    fetch_table_metadata,
    format_metadata_result,
    lambda_handler
)

class TestFireboltMetadataLambda:
    """Test cases for the Firebolt Metadata Lambda functions."""
    
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_aws_secret')
    def test_get_firebolt_credentials_success(self, mock_get_aws_secret):
        """Test retrieving Firebolt credentials from secrets manager."""
        # Set up mock
        mock_get_aws_secret.return_value = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "account_name": "test-account",
            "engine_name": "test-engine"
        }
        
        result = get_firebolt_credentials("firebolt-credentials", "us-east-1")
        
        assert "client_id" in result
        assert "client_secret" in result
        assert result["client_id"] == "test-client-id"
        assert result["client_secret"] == "test-client-secret"
        assert result["account_name"] == "test-account"
        assert result["engine_name"] == "test-engine"
    
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_aws_secret')
    def test_get_firebolt_credentials_missing_fields(self, mock_get_aws_secret):
        """Test handling missing required fields in credentials."""
        # Set up mock to return credentials without required fields
        mock_get_aws_secret.return_value = {"username": "test-user"}  # Missing client_id and client_secret
        
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
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        credentials = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret"
        }
        
        token = get_firebolt_access_token(credentials)
        
        assert token == "test-token-123"
    
    @patch('urllib.request.urlopen')
    def test_fetch_schema_metadata_success(self, mock_urlopen):
        """Test fetching schema metadata successfully."""
        # Mock response for schema metadata
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "metadata": [
                    {"name": "schema_name", "type": "STRING"},
                    {"name": "table_count", "type": "INTEGER"}
                ],
                "rows": [
                    ["analytics", 5],
                    ["staging", 3],
                    ["reporting", 7]
                ]
            }
        }).encode('utf-8')
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = fetch_schema_metadata(
            "test-token", 
            "test-account", 
            "test-engine"
        )
        
        # Verify the request
        mock_urlopen.assert_called_once()
        request = mock_urlopen.call_args[0][0]
        assert request.get_full_url() == "https://api.app.firebolt.io/query/test-account/test-engine"
        assert "SELECT schema_name" in json.loads(request.data)["query"].lower()
        
        # Check the resulting data
        assert "data" in result
        assert len(result["data"]["rows"]) == 3
        assert result["data"]["rows"][0][0] == "analytics"
        assert result["data"]["rows"][0][1] == 5
    
    @patch('urllib.request.urlopen')
    def test_fetch_schema_metadata_error(self, mock_urlopen):
        """Test handling errors when fetching schema metadata."""
        # Mock an error response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "error": "Database connection failed",
            "message": "Failed to connect to engine"
        }).encode('utf-8')
        mock_response.getcode.return_value = 500
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = fetch_schema_metadata(
            "test-token", 
            "test-account", 
            "test-engine"
        )
        
        # Verify we get back the error
        assert "error" in result
        assert result["error"] == "Database connection failed"
    
    @patch('urllib.request.urlopen')
    def test_fetch_table_metadata_success(self, mock_urlopen):
        """Test fetching table metadata successfully."""
        # Mock response for table metadata
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "metadata": [
                    {"name": "column_name", "type": "STRING"},
                    {"name": "column_type", "type": "STRING"},
                    {"name": "is_nullable", "type": "BOOLEAN"}
                ],
                "rows": [
                    ["id", "INTEGER", False],
                    ["name", "STRING", True],
                    ["created_at", "TIMESTAMP", True]
                ]
            }
        }).encode('utf-8')
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = fetch_table_metadata(
            "test-token", 
            "test-account", 
            "test-engine",
            "analytics",
            "users"
        )
        
        # Verify the request
        mock_urlopen.assert_called_once()
        request = mock_urlopen.call_args[0][0]
        assert request.get_full_url() == "https://api.app.firebolt.io/query/test-account/test-engine"
        query = json.loads(request.data)["query"].lower()
        assert "select" in query
        assert "information_schema.columns" in query
        assert "where table_schema" in query
        assert "and table_name" in query
        
        # Check the resulting data
        assert "data" in result
        assert len(result["data"]["rows"]) == 3
        assert result["data"]["rows"][0][0] == "id"
        assert result["data"]["rows"][0][1] == "INTEGER"
        assert result["data"]["rows"][0][2] is False
    
    def test_format_metadata_result_schemas(self):
        """Test formatting schema metadata results."""
        raw_result = {
            "data": {
                "metadata": [
                    {"name": "schema_name", "type": "STRING"},
                    {"name": "table_count", "type": "INTEGER"}
                ],
                "rows": [
                    ["analytics", 5],
                    ["staging", 3],
                    ["reporting", 7]
                ]
            }
        }
        
        result = format_metadata_result(raw_result, "schemas")
        
        assert result["success"] is True
        assert len(result["schemas"]) == 3
        assert result["schemas"][0]["schema_name"] == "analytics"
        assert result["schemas"][0]["table_count"] == 5
        assert result["count"] == 3
    
    def test_format_metadata_result_tables(self):
        """Test formatting table metadata results."""
        raw_result = {
            "data": {
                "metadata": [
                    {"name": "table_name", "type": "STRING"},
                    {"name": "column_count", "type": "INTEGER"},
                    {"name": "row_count_estimate", "type": "INTEGER"}
                ],
                "rows": [
                    ["users", 10, 5000],
                    ["orders", 8, 12000]
                ]
            }
        }
        
        result = format_metadata_result(raw_result, "tables")
        
        assert result["success"] is True
        assert len(result["tables"]) == 2
        assert result["tables"][0]["table_name"] == "users"
        assert result["tables"][0]["column_count"] == 10
        assert result["tables"][0]["row_count_estimate"] == 5000
        assert result["count"] == 2
    
    def test_format_metadata_result_columns(self):
        """Test formatting column metadata results."""
        raw_result = {
            "data": {
                "metadata": [
                    {"name": "column_name", "type": "STRING"},
                    {"name": "column_type", "type": "STRING"},
                    {"name": "is_nullable", "type": "BOOLEAN"}
                ],
                "rows": [
                    ["id", "INTEGER", False],
                    ["name", "STRING", True],
                    ["created_at", "TIMESTAMP", True]
                ]
            }
        }
        
        result = format_metadata_result(raw_result, "columns")
        
        assert result["success"] is True
        assert len(result["columns"]) == 3
        assert result["columns"][0]["column_name"] == "id"
        assert result["columns"][0]["column_type"] == "INTEGER"
        assert result["columns"][0]["is_nullable"] is False
        assert result["count"] == 3
    
    def test_format_metadata_result_error(self):
        """Test formatting error metadata results."""
        raw_result = {
            "error": "Permission denied",
            "message": "User does not have access to this resource"
        }
        
        result = format_metadata_result(raw_result, "schemas")
        
        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Permission denied"
        assert result["message"] == "User does not have access to this resource"
    
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_access_token')
    @patch('tools.firebolt.metadata_lambda.lambda_function.fetch_schema_metadata')
    def test_lambda_handler_list_schemas(self, mock_fetch_schema, mock_get_token, mock_get_creds):
        """Test lambda_handler with list_schemas operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "account_name": "test-account",
            "engine_name": "test-engine"
        }
        mock_get_token.return_value = "test-token"
        
        mock_schema_result = {
            "data": {
                "metadata": [
                    {"name": "schema_name", "type": "STRING"},
                    {"name": "table_count", "type": "INTEGER"}
                ],
                "rows": [
                    ["analytics", 5],
                    ["staging", 3]
                ]
            }
        }
        mock_fetch_schema.return_value = mock_schema_result
        
        # Test event for listing schemas
        event = {
            "operation": "list_schemas"
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["success"] is True
        assert len(result["schemas"]) == 2
        assert result["schemas"][0]["schema_name"] == "analytics"
        
        # Verify the calls
        mock_get_creds.assert_called_once()
        mock_get_token.assert_called_once()
        mock_fetch_schema.assert_called_once_with(
            "test-token", "test-account", "test-engine"
        )
    
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_access_token')
    @patch('tools.firebolt.metadata_lambda.lambda_function.fetch_table_metadata')
    def test_lambda_handler_list_tables(self, mock_fetch_table, mock_get_token, mock_get_creds):
        """Test lambda_handler with list_tables operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "account_name": "test-account",
            "engine_name": "test-engine"
        }
        mock_get_token.return_value = "test-token"
        
        mock_table_result = {
            "data": {
                "metadata": [
                    {"name": "table_name", "type": "STRING"},
                    {"name": "column_count", "type": "INTEGER"}
                ],
                "rows": [
                    ["users", 10],
                    ["orders", 8]
                ]
            }
        }
        mock_fetch_table.return_value = mock_table_result
        
        # Test event for listing tables in a schema
        event = {
            "operation": "list_tables",
            "schema": "analytics"
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["success"] is True
        assert len(result["tables"]) == 2
        assert result["tables"][0]["table_name"] == "users"
        
        # Verify the calls
        mock_get_creds.assert_called_once()
        mock_get_token.assert_called_once()
        mock_fetch_table.assert_called_once_with(
            "test-token", "test-account", "test-engine", 
            "analytics", None
        )
    
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_access_token')
    @patch('tools.firebolt.metadata_lambda.lambda_function.fetch_table_metadata')
    def test_lambda_handler_describe_table(self, mock_fetch_table, mock_get_token, mock_get_creds):
        """Test lambda_handler with describe_table operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "account_name": "test-account",
            "engine_name": "test-engine"
        }
        mock_get_token.return_value = "test-token"
        
        mock_column_result = {
            "data": {
                "metadata": [
                    {"name": "column_name", "type": "STRING"},
                    {"name": "column_type", "type": "STRING"}
                ],
                "rows": [
                    ["id", "INTEGER"],
                    ["name", "STRING"]
                ]
            }
        }
        mock_fetch_table.return_value = mock_column_result
        
        # Test event for describing a table
        event = {
            "operation": "describe_table",
            "schema": "analytics",
            "table": "users"
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["success"] is True
        assert len(result["columns"]) == 2
        assert result["columns"][0]["column_name"] == "id"
        assert result["columns"][0]["column_type"] == "INTEGER"
        
        # Verify the calls
        mock_get_creds.assert_called_once()
        mock_get_token.assert_called_once()
        mock_fetch_table.assert_called_once_with(
            "test-token", "test-account", "test-engine", 
            "analytics", "users"
        )
    
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_access_token')
    def test_lambda_handler_invalid_operation(self, mock_get_token, mock_get_creds):
        """Test lambda_handler with invalid operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret"
        }
        mock_get_token.return_value = "test-token"
        
        # Test event with invalid operation
        event = {
            "operation": "invalid_operation"
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result indicates an error
        assert result["success"] is False
        assert "Unsupported operation" in result["error"]
    
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.metadata_lambda.lambda_function.get_firebolt_access_token')
    def test_lambda_handler_missing_parameters(self, mock_get_token, mock_get_creds):
        """Test lambda_handler with missing required parameters."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret"
        }
        mock_get_token.return_value = "test-token"
        
        # Test event missing schema for describe_table operation
        event = {
            "operation": "describe_table",
            # Missing schema
            "table": "users"
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result indicates an error
        assert result["success"] is False
        assert "Missing required parameter" in result["error"]
