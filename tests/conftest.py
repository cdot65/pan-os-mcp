"""Test fixtures for the MCP server tests."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import create_connected_server_and_client_session

from palo_alto_mcp.config import Settings
from palo_alto_mcp.models import (
    AddressObject,
    SecurityZone,
    SystemInfo,
)
from palo_alto_mcp.server import mcp


@pytest.fixture
def mock_settings() -> Settings:
    """Provide mock settings for testing."""
    return Settings(
        panos_hostname="test-firewall.example.com",
        panos_api_key="TEST_API_KEY",
    )


@pytest.fixture
def mock_system_info() -> SystemInfo:
    """Provide mock system information for testing."""
    return SystemInfo(
        hostname="test-firewall",
        ip_address="192.168.1.1",
        netmask="255.255.255.0",
        default_gateway="192.168.1.254",
        mac_address="00:1B:17:00:01:01",
        time="Wed Mar 15 12:00:00 2024",
        uptime="0 days, 0:01:15",
        version="11.0.0",
        gp_version="6.0.0",
    )


@pytest.fixture
def mock_address_objects() -> list[AddressObject]:
    """Provide mock address objects for testing."""
    return [
        AddressObject(
            name="web-server",
            type="ip-netmask",
            value="192.168.1.100/32",
            description="Internal web server",
            location="vsys1",
            tags=["servers", "web"],
        ),
        AddressObject(
            name="db-server",
            type="ip-netmask",
            value="192.168.1.101/32",
            description="Internal database server",
            location="vsys1",
            tags=["servers", "db"],
        ),
    ]


@pytest.fixture
def mock_security_zones() -> list[SecurityZone]:
    """Provide mock security zones for testing."""
    return [
        SecurityZone(
            name="trust",
            type="layer3",
            location="vsys1",
            interfaces=["ethernet1/1"],
            user_identification=True,
            device_identification=True,
        ),
        SecurityZone(
            name="untrust",
            type="layer3",
            location="vsys1",
            interfaces=["ethernet1/2"],
            user_identification=False,
            device_identification=False,
        ),
    ]


@pytest.fixture
async def mock_panos_client() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mock PAN-OS API client for testing.

    Yields:
        An AsyncMock instance configured with test responses.
    """
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    yield client


@pytest.fixture
async def mcp_client() -> AsyncGenerator[Any, None]:
    """Create a connected MCP client session for integration testing.

    Yields:
        A connected MCP client session.
    """
    async with create_connected_server_and_client_session(mcp) as client:
        yield client
