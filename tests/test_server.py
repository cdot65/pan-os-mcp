"""Test suite for the MCP server implementation."""

import pytest
from httpx import AsyncClient

from palo_alto_mcp.config import Settings
from palo_alto_mcp.models import PANOSError, SystemInfo
from palo_alto_mcp.pan_os_api import PANOSClient


@pytest.mark.asyncio
async def test_show_system_info(
    mock_system_info: SystemInfo,
    mock_panos_client: PANOSClient,
    mcp_client: AsyncClient,
) -> None:
    """Test the show_system_info tool."""
    # Configure mock response
    mock_panos_client.get_system_info.return_value = mock_system_info

    # Call the tool
    response = await mcp_client.post("/show_system_info")
    result = response.json()

    # Verify the response
    assert "System Information" in result["content"]
    assert mock_system_info.hostname in result["content"]
    assert mock_system_info.version in result["content"]
    assert mock_system_info.uptime in result["content"]
    assert mock_system_info.gp_version in result["content"]


@pytest.mark.asyncio
async def test_show_system_info_error(
    mock_panos_client: PANOSClient,
    mcp_client: AsyncClient,
) -> None:
    """Test error handling in show_system_info tool."""
    # Configure mock to raise an error
    error_msg = "Failed to connect to firewall"
    mock_panos_client.get_system_info.side_effect = PANOSError(error_msg)

    # Call the tool
    response = await mcp_client.post("/show_system_info")
    result = response.json()

    # Verify error handling
    assert "Error (PANOSError):" in result["content"]
    assert error_msg in result["content"]


@pytest.mark.asyncio
async def test_retrieve_address_objects(
    mock_address_objects: list,
    mock_panos_client: PANOSClient,
    mcp_client: AsyncClient,
) -> None:
    """Test the retrieve_address_objects tool."""
    # Configure mock response
    mock_panos_client.get_address_objects.return_value = mock_address_objects

    # Call the tool
    response = await mcp_client.post("/retrieve_address_objects")
    result = response.json()

    # Verify the response
    assert "Address Objects" in result["content"]
    for obj in mock_address_objects:
        assert obj.name in result["content"]
        assert obj.type in result["content"]
        assert obj.value in result["content"]
        if obj.description:
            assert obj.description in result["content"]
        if obj.tags:
            for tag in obj.tags:
                assert tag in result["content"]


@pytest.mark.asyncio
async def test_retrieve_security_zones(
    mock_security_zones: list,
    mock_panos_client: PANOSClient,
    mcp_client: AsyncClient,
) -> None:
    """Test the retrieve_security_zones tool."""
    # Configure mock response
    mock_panos_client.get_security_zones.return_value = mock_security_zones

    # Call the tool
    response = await mcp_client.post("/retrieve_security_zones")
    result = response.json()

    # Verify the response
    assert "Security Zones" in result["content"]
    for zone in mock_security_zones:
        assert zone.name in result["content"]
        assert zone.type in result["content"]
        assert "User Identification: Enabled" in result["content"] if zone.user_identification else True
        assert "Device Identification: Enabled" in result["content"] if zone.device_identification else True
        if zone.interfaces:
            for interface in zone.interfaces:
                assert interface in result["content"]


@pytest.mark.asyncio
async def test_error_formatting(
    mock_panos_client: PANOSClient,
    mcp_client: AsyncClient,
) -> None:
    """Test error formatting across all tools."""
    error_msg = "Test error message"
    error_details = {"code": "TEST001", "suggestion": "Check configuration"}
    test_error = PANOSError(error_msg, error_details)

    # Configure mock to raise the error for all operations
    mock_panos_client.get_system_info.side_effect = test_error
    mock_panos_client.get_address_objects.side_effect = test_error
    mock_panos_client.get_security_zones.side_effect = test_error

    # Test error handling for each tool
    tools = [
        "/show_system_info",
        "/retrieve_address_objects",
        "/retrieve_security_zones",
    ]

    for tool_path in tools:
        response = await mcp_client.post(tool_path)
        result = response.json()

        # Verify error formatting
        assert "Error (PANOSError):" in result["content"]
        assert error_msg in result["content"]
        assert "Details:" in result["content"]
        for key, value in error_details.items():
            assert f"- {key}: {value}" in result["content"]


@pytest.mark.asyncio
async def test_check_health(
    mock_settings: Settings,  # Keep this as it's used in the test
    mock_system_info: SystemInfo,
    mock_panos_client: PANOSClient,
    mcp_client: AsyncClient,
) -> None:
    """Test the check_health tool."""
    # Configure mock response
    mock_panos_client.get_system_info.return_value = mock_system_info

    # Call the tool
    response = await mcp_client.post("/check_health")
    result = response.json()

    # Verify the response
    assert "PAN-OS MCP Server Health Check" in result["content"]
    assert "MCP Server Version" in result["content"]
    assert f"Target Firewall: {mock_settings.panos_hostname}" in result["content"]
    assert "Debug Mode: Enabled" in result["content"]
    assert "Connection Status: Connected" in result["content"]
    assert mock_system_info.hostname in result["content"]
    assert mock_system_info.version in result["content"]
    assert mock_system_info.uptime in result["content"]
    if mock_system_info.gp_version:
        assert mock_system_info.gp_version in result["content"]


@pytest.mark.asyncio
async def test_check_health_error(
    mock_settings: Settings,  # Keep this as it's used in the test
    mock_panos_client: PANOSClient,
    mcp_client: AsyncClient,
) -> None:
    """Test error handling in check_health tool."""
    # Configure mock to raise an error
    error_msg = "Failed to connect to firewall"
    mock_panos_client.get_system_info.side_effect = PANOSError(error_msg)

    # Call the tool
    response = await mcp_client.post("/check_health")
    result = response.json()

    # Verify error handling
    assert "PAN-OS MCP Server Health Check" in result["content"]
    assert "MCP Server Version" in result["content"]
    assert f"Target Firewall: {mock_settings.panos_hostname}" in result["content"]
    assert "Debug Mode: Enabled" in result["content"]
    assert "Connection Status: Error" in result["content"]
    assert error_msg in result["content"]
