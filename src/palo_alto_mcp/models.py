"""Models for the Palo Alto Networks MCP Server.

This module contains Pydantic models for request/response validation and custom exceptions
for error handling.
"""

from typing import Literal

from pydantic import BaseModel, Field


class SystemInfo(BaseModel):
    """Model for system information."""

    hostname: str = Field(..., description="System hostname")
    ip_address: str = Field(..., description="Management IP address")
    netmask: str = Field(..., description="Management netmask")
    default_gateway: str = Field(..., description="Default gateway")
    mac_address: str = Field(..., description="Management MAC address")
    time: str = Field(..., description="System time")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="PAN-OS version")
    gp_version: str | None = Field(None, description="GlobalProtect version")


class AddressObject(BaseModel):
    """Model for address objects."""

    name: str = Field(..., description="Name of the address object")
    type: Literal["ip-netmask", "ip-range", "fqdn"] = Field(..., description="Type of address object")
    value: str = Field(..., description="Value of the address object")
    description: str | None = Field(None, description="Object description")
    location: str = Field("vsys1", description="Location of the object (e.g., vsys1)")
    tags: list[str] | None = Field(default=[], description="Associated tags")


class SecurityZone(BaseModel):
    """Model for security zones."""

    name: str = Field(..., description="Name of the zone")
    type: Literal["layer3", "layer2", "virtual-wire", "tap"] = Field(..., description="Type of zone")
    location: str = Field("vsys1", description="Location of the zone")
    interfaces: list[str] | None = Field(default=[], description="Interfaces in the zone")
    user_identification: bool = Field(False, description="Whether user identification is enabled")
    device_identification: bool = Field(False, description="Whether device identification is enabled")
    packet_buffer_protection: bool = Field(False, description="Whether packet buffer protection is enabled")


class SecurityPolicy(BaseModel):
    """Model for security policies."""

    name: str = Field(..., description="Name of the security policy")
    source_zones: list[str] = Field(default=[], description="Source zones")
    source_addresses: list[str] = Field(default=[], description="Source addresses")
    destination_zones: list[str] = Field(default=[], description="Destination zones")
    destination_addresses: list[str] = Field(default=[], description="Destination addresses")
    applications: list[str] = Field(default=[], description="Applications")
    services: list[str] = Field(default=[], description="Services")
    action: Literal["allow", "deny", "drop", "reset"] = Field(..., description="Action to take")
    description: str | None = Field(None, description="Policy description")
    enabled: bool = Field(True, description="Whether the policy is enabled")
    location: str = Field("vsys1", description="Location of the policy")


# Custom Exceptions
class PanosError(Exception):
    """Base exception for PAN-OS related errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PanosConnectionError(PanosError):
    """Raised when there's an error connecting to the PAN-OS device."""

    pass


class PanosAuthenticationError(PanosError):
    """Raised when there's an authentication error with the PAN-OS device."""

    pass


class PanosConfigurationError(PanosError):
    """Raised when there's an error in the PAN-OS configuration."""

    pass


class PanosOperationError(PanosError):
    """Raised when a PAN-OS operation fails."""

    pass
