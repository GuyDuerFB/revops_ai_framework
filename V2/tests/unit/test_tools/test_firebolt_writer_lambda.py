"""
Unit tests for the Firebolt Writer Lambda component.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the module under test
from tools.firebolt.writer_lambda.lambda_function import (
    get_firebolt_credentials,
    get_firebolt_access_token,
    execute_firebolt_write,
    perform_insert,
    perform_update,
    perform_delete,
    format_operation_result,
    lambda_handler
)

class TestFireboltWriterLambda:
    """Test cases for the Firebolt Writer Lambda functions."""
    
    @patch('tools.firebolt.writer_lambda.lambda_function.get_aws_secret')
    def test_get_firebolt_credentials(self, mock_get_aws_secret):
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
    
    @patch('tools.firebolt.writer_lambda.lambda_function.get_aws_secret')
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
        
        # Verify the request was made correctly
        mock_urlopen.assert_called_once()
        request_arg = mock_urlopen.call_args[0][0]
        assert request_arg.get_full_url() == "https://id.app.firebolt.io/oauth/token"
        assert b"grant_type=client_credentials" in request_arg.data
        assert b"client_id=test-client-id" in request_arg.data
        assert b"client_secret=test-client-secret" in request_arg.data
    
    @patch('urllib.request.urlopen')
    def test_get_firebolt_access_token_error(self, mock_urlopen):
        """Test handling errors when getting a Firebolt access token."""
        # Mock the response with an error
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "error": "invalid_client",
            "error_description": "Invalid client credentials"
        }).encode('utf-8')
        mock_response.getcode.return_value = 401
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        credentials = {
            "client_id": "invalid-id",
            "client_secret": "invalid-secret"
        }
        
        with pytest.raises(Exception) as excinfo:
            get_firebolt_access_token(credentials)
        
        assert "Failed to get Firebolt access token" in str(excinfo.value)
        assert "401" in str(excinfo.value)
    
    def test_perform_insert_success(self):
        """Test constructing an INSERT query."""
        table_name = "test_table"
        data = [
            {"id": 1, "name": "Test 1", "active": True},
            {"id": 2, "name": "Test 2", "active": False}
        ]
        
        query, values = perform_insert(table_name, data)
        
        # Check the generated query
        assert query.startswith("INSERT INTO test_table")
        assert "(id, name, active)" in query
        assert "VALUES" in query
        
        # Check the values
        assert len(values) == 2
        assert values[0]["id"] == 1
        assert values[0]["name"] == "Test 1"
        assert values[0]["active"] is True
        assert values[1]["id"] == 2
        assert values[1]["name"] == "Test 2"
        assert values[1]["active"] is False
    
    def test_perform_insert_no_data(self):
        """Test handling empty data in INSERT operation."""
        with pytest.raises(ValueError) as excinfo:
            perform_insert("test_table", [])
        
        assert "No data provided for insert operation" in str(excinfo.value)
    
    def test_perform_update_success(self):
        """Test constructing an UPDATE query."""
        table_name = "test_table"
        data = {"name": "Updated Name", "active": False}
        condition = "id = 1"
        
        query = perform_update(table_name, data, condition)
        
        # Check the generated query
        assert query.startswith("UPDATE test_table SET")
        assert "name = 'Updated Name'" in query
        assert "active = FALSE" in query
        assert "WHERE id = 1" in query
    
    def test_perform_update_no_data(self):
        """Test handling empty data in UPDATE operation."""
        with pytest.raises(ValueError) as excinfo:
            perform_update("test_table", {}, "id = 1")
        
        assert "No data provided for update operation" in str(excinfo.value)
    
    def test_perform_update_no_condition(self):
        """Test handling missing condition in UPDATE operation."""
        with pytest.raises(ValueError) as excinfo:
            perform_update("test_table", {"name": "Test"}, "")
        
        assert "No condition provided for update operation" in str(excinfo.value)
    
    def test_perform_delete_success(self):
        """Test constructing a DELETE query."""
        table_name = "test_table"
        condition = "id = 1"
        
        query = perform_delete(table_name, condition)
        
        # Check the generated query
        assert query == "DELETE FROM test_table WHERE id = 1"
    
    def test_perform_delete_no_condition(self):
        """Test handling missing condition in DELETE operation."""
        with pytest.raises(ValueError) as excinfo:
            perform_delete("test_table", "")
        
        assert "No condition provided for delete operation" in str(excinfo.value)
    
    def test_format_operation_result_success(self):
        """Test formatting successful operation results."""
        raw_result = {
            "data": {
                "affected_rows": 5,
                "metadata": [],
                "rows": []
            }
        }
        
        result = format_operation_result(raw_result)
        
        assert result["success"] is True
        assert result["rows_affected"] == 5
    
    def test_format_operation_result_error(self):
        """Test formatting error results."""
        raw_result = {
            "error": "SQL syntax error",
            "message": "Invalid SQL statement"
        }
        
        result = format_operation_result(raw_result)
        
        assert result["success"] is False
        assert result["error"] == "SQL syntax error"
        assert result["message"] == "Invalid SQL statement"
    
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_access_token')
    @patch('tools.firebolt.writer_lambda.lambda_function.execute_firebolt_write')
    def test_lambda_handler_insert(self, mock_execute, mock_get_token, mock_get_creds):
        """Test lambda_handler with insert operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "account_name": "test-account",
            "engine_name": "test-engine"
        }
        mock_get_token.return_value = "test-token"
        mock_execute.return_value = {"success": True, "rows_affected": 2}
        
        # Test event
        event = {
            "table": "insights",
            "operation": "insert",
            "data": [
                {"id": 1, "value": "test1"},
                {"id": 2, "value": "test2"}
            ]
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["success"] is True
        assert result["rows_affected"] == 2
        
        # Check that execute_firebolt_write was called with correct parameters
        mock_execute.assert_called_once()
        # We don't check the exact query because it's built inside the function
        assert mock_execute.call_args[0][1] == "test-token"
        assert mock_execute.call_args[0][2] == "test-account"
        assert mock_execute.call_args[0][3] == "test-engine"
    
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_access_token')
    @patch('tools.firebolt.writer_lambda.lambda_function.execute_firebolt_write')
    def test_lambda_handler_update(self, mock_execute, mock_get_token, mock_get_creds):
        """Test lambda_handler with update operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "account_name": "test-account",
            "engine_name": "test-engine"
        }
        mock_get_token.return_value = "test-token"
        mock_execute.return_value = {"success": True, "rows_affected": 1}
        
        # Test event
        event = {
            "table": "insights",
            "operation": "update",
            "data": {"value": "updated"},
            "condition": "id = 1"
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["success"] is True
        assert result["rows_affected"] == 1
    
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_access_token')
    @patch('tools.firebolt.writer_lambda.lambda_function.execute_firebolt_write')
    def test_lambda_handler_delete(self, mock_execute, mock_get_token, mock_get_creds):
        """Test lambda_handler with delete operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "account_name": "test-account",
            "engine_name": "test-engine"
        }
        mock_get_token.return_value = "test-token"
        mock_execute.return_value = {"success": True, "rows_affected": 1}
        
        # Test event
        event = {
            "table": "insights",
            "operation": "delete",
            "condition": "id = 1"
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["success"] is True
        assert result["rows_affected"] == 1
    
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_access_token')
    def test_lambda_handler_invalid_operation(self, mock_get_token, mock_get_creds):
        """Test lambda_handler with an invalid operation."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret"
        }
        mock_get_token.return_value = "test-token"
        
        # Test event with invalid operation
        event = {
            "table": "insights",
            "operation": "invalid_operation",
            "data": {"id": 1}
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result indicates an error
        assert result["success"] is False
        assert "Unsupported operation" in result["error"]
    
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_credentials')
    @patch('tools.firebolt.writer_lambda.lambda_function.get_firebolt_access_token')
    def test_lambda_handler_missing_parameters(self, mock_get_token, mock_get_creds):
        """Test lambda_handler with missing required parameters."""
        # Setup mocks
        mock_get_creds.return_value = {
            "client_id": "test-id",
            "client_secret": "test-secret"
        }
        mock_get_token.return_value = "test-token"
        
        # Test event with missing table name
        event = {
            "operation": "insert",
            "data": {"id": 1}
            # Missing table
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result indicates an error
        assert result["success"] is False
        assert "Missing required parameter" in result["error"]
