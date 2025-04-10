# Testing Strategy

This document outlines a recommended testing strategy for the Palo Alto Networks MCP Server.

## Unit Tests

Unit tests focus on testing individual functions and classes in isolation.

### Testing the PAN-OS API Client

The `PanosApiClient` class should be tested with mocked HTTP responses to avoid making actual API calls during testing.

```python
import pytest
import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, patch

from palo_alto_mcp.config import Settings
from palo_alto_mcp.pan_os_api import PanosApiClient

@pytest.mark.asyncio
async def test_get_address_objects():
    # Create mock settings
    settings = Settings(
        panos_hostname="firewall.example.com",
        panos_api_key="mock-api-key"
    )

    # Create mock XML response
    xml_response = """
    <response status="success">
        <result>
            <address>
                <entry name="test-address">
                    <ip-netmask>192.168.1.1/32</ip-netmask>
                    <description>Test address</description>
                </entry>
            </address>
        </result>
    </response>
    """

    # Mock the HTTP client
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get = AsyncMock()
        mock_instance.get.return_value.text = xml_response
        mock_instance.get.return_value.raise_for_status = AsyncMock()

        # Create client and call method
        async with PanosApiClient(settings) as client:
            address_objects = await client.get_address_objects()

        # Assert results
        assert len(address_objects) == 1
        assert address_objects[0]["name"] == "test-address"
        assert address_objects[0]["type"] == "ip-netmask"
        assert address_objects[0]["value"] == "192.168.1.1/32"
        assert address_objects[0]["description"] == "Test address"
```

### Testing the Server Tools

The server tools should be tested with a mocked `PanosApiClient`.

```python
import pytest
from unittest.mock import AsyncMock, patch

from palo_alto_mcp.server import retrieve_address_objects

@pytest.mark.asyncio
async def test_retrieve_address_objects():
    # Mock the PanosApiClient
    with patch("palo_alto_mcp.server.PanosApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock the get_address_objects method
        mock_client.get_address_objects.return_value = [
            {
                "name": "test-address",
                "type": "ip-netmask",
                "value": "192.168.1.1/32",
                "description": "Test address"
            }
        ]

        # Call the tool function
        result = await retrieve_address_objects(None)

        # Assert the result contains the expected information
        assert "test-address" in result
        assert "192.168.1.1/32" in result
        assert "Test address" in result
```

## Integration Tests

Integration tests focus on testing the interaction between different components of the system.

### Testing the MCP Server

The MCP server can be tested using the SDK's `create_connected_server_and_client_session` function.

```python
import pytest
from mcp.server.testing import create_connected_server_and_client_session
from mcp.client import Client

from palo_alto_mcp.server import mcp

@pytest.mark.asyncio
async def test_mcp_server():
    # Create a connected server and client session
    async with create_connected_server_and_client_session(mcp) as client:
        # List available tools
        tools = await client.list_tools()

        # Assert that the expected tools are available
        tool_names = [tool.name for tool in tools]
        assert "show_system_info" in tool_names
        assert "retrieve_address_objects" in tool_names
        assert "retrieve_security_zones" in tool_names
        assert "retrieve_security_policies" in tool_names
```

## End-to-End (E2E) Tests

End-to-end tests focus on testing complete workflows, potentially involving real Palo Alto Networks firewalls.

!!! warning
    E2E tests should be run in a controlled environment with a dedicated test firewall to avoid impacting production systems.

### Testing with a Real Firewall

```python
import pytest
import os
from mcp.server.testing import create_connected_server_and_client_session
from mcp.client import Client

from palo_alto_mcp.server import mcp

@pytest.mark.e2e
@pytest.mark.skipif(not os.environ.get("E2E_TEST"), reason="E2E tests disabled")
@pytest.mark.asyncio
async def test_e2e_retrieve_address_objects():
    # Create a connected server and client session
    async with create_connected_server_and_client_session(mcp) as client:
        # Call the retrieve_address_objects tool
        result = await client.call_tool("retrieve_address_objects")

        # Assert that the result is not empty
        assert result.content
        assert "# Palo Alto Networks Firewall Address Objects" in result.content
```

## Testing Tools and Frameworks

- **pytest**: The primary testing framework
- **pytest-asyncio**: For testing asynchronous code
- **unittest.mock**: For mocking dependencies
- **httpx**: For making HTTP requests in tests
- **mcp.server.testing**: For testing MCP servers

## Continuous Integration (CI)

Tests should be incorporated into a CI pipeline (e.g., GitHub Actions, GitLab CI) to ensure that they are run automatically on every commit.

### Example GitHub Actions Workflow

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        pytest
```

## Test Coverage

Test coverage should be monitored to ensure that all parts of the codebase are adequately tested.

```bash
pytest --cov=palo_alto_mcp
```

## Mocking Strategies

### Mocking HTTP Responses

HTTP responses can be mocked using `unittest.mock` to patch the `httpx.AsyncClient` class.

### Mocking the Palo Alto Networks XML API

The Palo Alto Networks XML API can be mocked by providing pre-defined XML responses for different API calls.

### Mocking MCP Clients

MCP clients can be mocked using the SDK's testing utilities.
