# RevOps AI Framework V2 - Tests

This directory contains test suites for validating the functionality, performance, and reliability of the RevOps AI Framework.

## Overview

The tests directory provides comprehensive test coverage for all components of the RevOps AI Framework, including unit tests, integration tests, and end-to-end scenarios. These tests ensure the quality and correctness of the framework and help prevent regressions during development.

## Directory Structure

```
tests/
├── README.md               # This file
├── conftest.py             # PyTest configuration and fixtures
├── unit/                   # Unit tests for individual components
│   ├── test_agents/        # Tests for agent components
│   └── test_tools/         # Tests for tool implementations
└── integration/            # Integration tests across components
    ├── test_agent_integration/   # Tests for agent interactions
    ├── test_agents/          # Tests for individual agents
    ├── test_deployment/      # Tests for deployment processes
    └── test_flow_integration/ # Tests for flow integration
```

## Running Tests

### Prerequisites

- Python 3.8+
- pip dependencies installed (`pip install -r requirements-dev.txt`)
- AWS credentials configured for integration tests (if applicable)
- Mock services started (for certain integration tests)

### Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit

# Run specific test module
pytest tests/unit/agents/test_data_agent.py

# Run with coverage report
pytest tests/unit --cov=V2
```

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration

# Run specific integration test category
pytest tests/integration/flow_execution

# Run integration tests with AWS resources
AWS_PROFILE=test-profile pytest tests/integration/external_systems
```

### Running Performance Tests

```bash
# Run performance tests (may take longer)
pytest tests/performance
```

## Test Configuration

Test configuration is managed through:

1. **conftest.py**: Global fixture definitions and test setup
2. **environment variables**: Configuration for external services
3. **pytest.ini**: PyTest configuration settings

### Configuration Example

```ini
# pytest.ini
[pytest]
markers =
    unit: unit tests
    integration: integration tests
    slow: tests that take longer to run
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
```

## Writing Tests

### Unit Test Example

```python
# tests/unit/agents/test_data_agent.py
import pytest
from unittest.mock import patch, MagicMock
from agents.data_agent.agent import DataAgent

class TestDataAgent:
    @pytest.fixture
    def data_agent(self):
        """Create a data agent instance for testing"""
        return DataAgent()
    
    def test_process_query(self, data_agent):
        """Test that the data agent processes queries correctly"""
        # Arrange
        mock_data = {"customer_id": "cust-123", "revenue": 10000}
        with patch('agents.data_agent.connectors.firebolt.FireboltConnector.execute_query',
                  return_value=mock_data):
            # Act
            result = data_agent.process({
                "data_source": "firebolt",
                "query": "get_customer_revenue",
                "parameters": {"customer_id": "cust-123"}
            })
            
            # Assert
            assert result["success"] is True
            assert result["data"]["customer_id"] == "cust-123"
            assert result["data"]["revenue"] == 10000
```

### Integration Test Example

```python
# tests/integration/agent_interactions/test_data_decision_integration.py
import pytest
from agents.data_agent.agent import DataAgent
from agents.decision_agent.agent import DecisionAgent

class TestDataDecisionIntegration:
    @pytest.fixture
    def agents(self):
        """Create instances of the required agents"""
        return {
            "data": DataAgent(),
            "decision": DecisionAgent()
        }
    
    @pytest.mark.integration
    def test_data_to_decision_flow(self, agents):
        """Test the data retrieval to decision making flow"""
        # Step 1: Retrieve data
        data_result = agents["data"].process({
            "data_source": "test_source",
            "query": "get_test_data",
            "parameters": {"test_param": "value"}
        })
        
        assert data_result["success"] is True
        
        # Step 2: Make decision based on data
        decision_result = agents["decision"].process({
            "decision_type": "test_decision",
            "input_data": data_result["data"]
        })
        
        assert decision_result["success"] is True
        assert "recommendation" in decision_result
        assert decision_result["confidence_score"] > 0.7
```

## Mock Services

For integration testing without dependencies on external systems, the test suite includes mock implementations of:

- Mock Firebolt Database
- Mock Gong API
- Mock CRM System
- Mock Webhook Endpoints

These are defined in `tests/fixtures/mock_services/`.

## Test Coverage

Test coverage reports are generated with pytest-cov and can be viewed as HTML:

```bash
pytest --cov=V2 --cov-report=html
# Then open htmlcov/index.html
```

## Continuous Integration

Tests are automatically run in the CI/CD pipeline:

1. Unit tests run on all pull requests
2. Integration tests run on merges to main branch
3. Performance tests run on a scheduled basis

## Troubleshooting Tests

Common issues and solutions:

- **Missing Credentials**: Ensure AWS credentials are configured for tests that require them
- **Mocked Services Not Running**: Check if required mock services are started
- **Timeout Issues**: Some integration tests have timeouts, check service availability
- **Environment Conflicts**: Use a clean virtual environment to avoid dependency conflicts
