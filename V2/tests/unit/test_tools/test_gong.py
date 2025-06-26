"""
Unit tests for the Gong integration component.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the module under test
from tools.gong.gong_api import (
    GongAPI,
    get_gong_credentials,
    format_call_data
)

class TestGongAPI:
    """Test cases for the Gong API integration."""
    
    @pytest.fixture
    def sample_gong_credentials(self):
        """Fixture providing sample Gong API credentials for testing."""
        return {
            "access_key": "test-access-key",
            "access_key_secret": "test-access-key-secret",
            "base_url": "https://api.gong.io/v2"
        }
    
    @patch('tools.gong.gong_api.get_aws_secret')
    def test_get_gong_credentials_success(self, mock_get_aws_secret):
        """Test retrieving Gong credentials from AWS Secrets Manager."""
        # Set up mock response
        mock_get_aws_secret.return_value = {
            "access_key": "test-access-key",
            "access_key_secret": "test-access-key-secret"
        }
        
        result = get_gong_credentials("gong-credentials", "us-east-1")
        
        # Verify the response contains the expected fields
        assert result["access_key"] == "test-access-key"
        assert result["access_key_secret"] == "test-access-key-secret"
        assert "base_url" in result  # Should add default base URL
    
    @patch('tools.gong.gong_api.get_aws_secret')
    def test_get_gong_credentials_missing_fields(self, mock_get_aws_secret):
        """Test handling missing required fields in Gong credentials."""
        # Set up mock to return credentials without required fields
        mock_get_aws_secret.return_value = {"username": "test-user"}  # Missing access_key and access_key_secret
        
        with pytest.raises(Exception) as excinfo:
            get_gong_credentials("gong-credentials", "us-east-1")
        
        assert "Missing required fields" in str(excinfo.value)
    
    def test_gong_api_initialization(self, sample_gong_credentials):
        """Test initializing the GongAPI class."""
        api = GongAPI(sample_gong_credentials)
        
        assert api.access_key == "test-access-key"
        assert api.access_key_secret == "test-access-key-secret"
        assert api.base_url == "https://api.gong.io/v2"
    
    def test_format_call_data(self):
        """Test formatting raw call data from Gong API."""
        raw_call_data = {
            "calls": [
                {
                    "id": "call-123",
                    "title": "Product Demo with Acme Corp",
                    "parties": [
                        {"name": "John Doe", "email": "john@example.com", "role": "primary_speaker"},
                        {"name": "Jane Smith", "email": "jane@acmecorp.com", "role": "customer"}
                    ],
                    "duration": 3600,  # 1 hour in seconds
                    "scheduledTime": "2023-06-15T14:00:00Z",
                    "transcript": "This is the call transcript...",
                    "topics": [
                        {"topic": "pricing", "occurrences": 5},
                        {"topic": "features", "occurrences": 12}
                    ]
                }
            ]
        }
        
        formatted_data = format_call_data(raw_call_data)
        
        # Check the formatting
        assert len(formatted_data) == 1
        call = formatted_data[0]
        assert call["id"] == "call-123"
        assert call["title"] == "Product Demo with Acme Corp"
        assert call["duration_minutes"] == 60  # Converted to minutes
        assert call["date"] == "2023-06-15"
        assert call["speakers"] == ["John Doe", "Jane Smith"]
        assert "transcript" in call
        assert len(call["key_topics"]) == 2
        assert call["key_topics"][0]["topic"] == "pricing"
    
    @patch('requests.get')
    def test_list_calls_success(self, mock_get, sample_gong_credentials):
        """Test successfully listing calls from Gong API."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "calls": [
                {
                    "id": "call-123",
                    "title": "Product Demo",
                    "duration": 1800,
                    "scheduledTime": "2023-06-15T10:00:00Z"
                },
                {
                    "id": "call-456",
                    "title": "Follow-up Meeting",
                    "duration": 900,
                    "scheduledTime": "2023-06-16T15:30:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Create api instance
        api = GongAPI(sample_gong_credentials)
        
        # Call list_calls method
        params = {"from": "2023-06-01", "to": "2023-06-30"}
        result = api.list_calls(params)
        
        # Verify the request
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        assert call_args["url"] == "https://api.gong.io/v2/calls"
        assert call_args["params"] == params
        assert "auth" in call_args
        
        # Verify the result
        assert len(result) == 2
        assert result[0]["id"] == "call-123"
        assert result[1]["id"] == "call-456"
    
    @patch('requests.get')
    def test_list_calls_error(self, mock_get, sample_gong_credentials):
        """Test handling errors when listing calls from Gong API."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "Unauthorized",
            "message": "Invalid access key"
        }
        mock_get.return_value = mock_response
        
        # Create api instance
        api = GongAPI(sample_gong_credentials)
        
        # Call list_calls method with error expectation
        with pytest.raises(Exception) as excinfo:
            api.list_calls({"from": "2023-06-01", "to": "2023-06-30"})
        
        assert "Failed to list calls" in str(excinfo.value)
        assert "401" in str(excinfo.value)
    
    @patch('requests.get')
    def test_get_call_details_success(self, mock_get, sample_gong_credentials):
        """Test successfully getting call details from Gong API."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "callId": "call-123",
            "title": "Product Demo with Acme Corp",
            "duration": 3600,
            "transcript": "This is the detailed transcript...",
            "sentimentScores": {
                "average": 0.85,
                "beginning": 0.75,
                "end": 0.9
            },
            "speakers": [
                {"name": "John Doe", "role": "salesperson"},
                {"name": "Jane Smith", "role": "prospect"}
            ],
            "topics": ["pricing", "features", "competition"]
        }
        mock_get.return_value = mock_response
        
        # Create api instance
        api = GongAPI(sample_gong_credentials)
        
        # Call get_call_details method
        call_id = "call-123"
        result = api.get_call_details(call_id)
        
        # Verify the request
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        assert call_args["url"] == f"https://api.gong.io/v2/calls/{call_id}"
        assert "auth" in call_args
        
        # Verify the result
        assert result["callId"] == "call-123"
        assert result["title"] == "Product Demo with Acme Corp"
        assert "transcript" in result
        assert len(result["speakers"]) == 2
        assert result["sentimentScores"]["average"] == 0.85
    
    @patch('requests.get')
    def test_get_call_transcript_success(self, mock_get, sample_gong_credentials):
        """Test successfully getting call transcript from Gong API."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "callId": "call-123",
            "transcript": [
                {
                    "speakerName": "John Doe",
                    "speakerEmail": "john@example.com",
                    "text": "Hello, thank you for joining today's demo.",
                    "startTime": 0,
                    "endTime": 5
                },
                {
                    "speakerName": "Jane Smith",
                    "speakerEmail": "jane@acmecorp.com",
                    "text": "Thanks for having me. I'm interested in learning more about your product.",
                    "startTime": 6,
                    "endTime": 12
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Create api instance
        api = GongAPI(sample_gong_credentials)
        
        # Call get_call_transcript method
        call_id = "call-123"
        result = api.get_call_transcript(call_id)
        
        # Verify the request
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        assert call_args["url"] == f"https://api.gong.io/v2/calls/{call_id}/transcript"
        assert "auth" in call_args
        
        # Verify the result
        assert result["callId"] == "call-123"
        assert len(result["transcript"]) == 2
        assert result["transcript"][0]["speakerName"] == "John Doe"
        assert "Hello, thank you for joining" in result["transcript"][0]["text"]
    
    @patch('tools.gong.gong_api.get_gong_credentials')
    @patch('tools.gong.gong_api.GongAPI')
    def test_lambda_handler_list_calls(self, mock_gong_api_class, mock_get_credentials):
        """Test lambda_handler with list_calls operation."""
        # Setup mocks
        mock_get_credentials.return_value = {
            "access_key": "test-key",
            "access_key_secret": "test-secret"
        }
        
        mock_api = MagicMock()
        mock_api.list_calls.return_value = [
            {"id": "call-123", "title": "Test Call 1"},
            {"id": "call-456", "title": "Test Call 2"}
        ]
        mock_gong_api_class.return_value = mock_api
        
        # Create event for list_calls
        event = {
            "operation": "list_calls",
            "parameters": {
                "from": "2023-06-01",
                "to": "2023-06-30"
            }
        }
        
        # Import lambda_handler function locally to avoid circular import in test
        from tools.gong.lambda_function import lambda_handler
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["success"] is True
        assert len(result["calls"]) == 2
        assert result["calls"][0]["id"] == "call-123"
