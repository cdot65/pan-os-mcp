"""Palo Alto Networks MCP Server implementation using FastMCP."""

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.utilities.logging import get_logger

from palo_alto_mcp.config import get_settings
from palo_alto_mcp.models import (
    AddressObject,
    PanosError,
    SecurityZone,
    SystemInfo,
)
from palo_alto_mcp.pan_os_api import PanosApiClient

# Configure logging using MCP's structured logging
logger = get_logger(__name__)

# Create FastMCP instance
mcp = FastMCP(
    "PaloAltoMCPServer",
    description="MCP Server for interacting with Palo Alto Networks firewalls",
    version="0.1.0",  # Add version information
)


def format_error_response(error: Exception) -> str:
    """Format an error response in a consistent way.

    Args:
        error: The exception that occurred

    Returns:
        A formatted error message string
    """
    if isinstance(error, PanosError):
        error_type = error.__class__.__name__
        formatted_msg = f"Error ({error_type}): {str(error)}\n"
        if error.details:
            formatted_msg += "\nDetails:\n"
            for key, value in error.details.items():
                formatted_msg += f"- {key}: {value}\n"
        return formatted_msg
    return f"Error: {str(error)}"


@mcp.tool()
async def check_health(ctx: Context) -> str:
    """Check the health of the MCP server and PAN-OS connectivity.

    Args:
        ctx: The MCP context object for request-specific logging

    Returns:
        A formatted string containing health check information.

    Raises:
        PanosConnectionError: If connection to the firewall fails
        PanosAuthenticationError: If authentication fails
        PanosOperationError: If the operation fails
    """
    logger.info("Performing health check", context=ctx)

    try:
        settings = get_settings()
        health_info = [
            "# PAN-OS MCP Server Health Check\n",
            f"- **MCP Server Version**: {mcp.version}",
            f"- **Target Firewall**: {settings.panos_hostname}",
            "- **Debug Mode**: " + ("Enabled" if settings.debug else "Disabled"),
        ]

        # Test connectivity by getting system info
        async with PanosApiClient(settings) as client:
            system_info_dict = await client.get_system_info()
            system_info = SystemInfo(**system_info_dict)

            health_info.extend(
                [
                    "\n## Firewall Information",
                    f"- **Hostname**: {system_info.hostname}",
                    f"- **Model**: {system_info.model}",
                    f"- **PAN-OS Version**: {system_info.version}",
                    f"- **Uptime**: {system_info.uptime}",
                    "- **Connection Status**: Connected",
                ]
            )

            if system_info.gp_version:
                health_info.append(
                    f"- **GlobalProtect Version**: {system_info.gp_version}"
                )

        return "\n".join(health_info)

    except PanosError as e:
        logger.error(
            "Health check failed",
            error=str(e),
            error_type=e.__class__.__name__,
            details=getattr(e, "details", {}),
            context=ctx,
        )
        return "\n".join(
            [
                "# PAN-OS MCP Server Health Check\n",
                f"- **MCP Server Version**: {mcp.version}",
                f"- **Target Firewall**: {settings.panos_hostname}",
                "- **Debug Mode**: " + ("Enabled" if settings.debug else "Disabled"),
                "\n## Connection Status",
                "- **Status**: Failed",
                f"- **Error**: {str(e)}",
            ]
        )
    except Exception as e:
        logger.error(
            "Unexpected error during health check",
            error=str(e),
            context=ctx,
        )
        return format_error_response(e)


@mcp.tool()
async def show_system_info(ctx: Context) -> str:
    """Get system information from the Palo Alto Networks firewall.

    Args:
        ctx: The MCP context object for request-specific logging

    Returns:
        A formatted string containing system information.

    Raises:
        PanosConnectionError: If connection to the firewall fails
        PanosAuthenticationError: If authentication fails
        PanosOperationError: If the operation fails
    """
    logger.info("Retrieving system information", context=ctx)

    try:
        settings = get_settings()
        async with PanosApiClient(settings) as client:
            system_info_dict = await client.get_system_info()

        # Validate response using our model
        system_info = SystemInfo(**system_info_dict)

        # Format the system information as a readable string
        formatted_info = "# Palo Alto Networks Firewall System Information\n\n"
        for field_name, field_value in system_info.model_dump().items():
            if field_value is not None:  # Only show non-None values
                formatted_name = field_name.replace("_", " ").title()
                formatted_info += f"**{formatted_name}**: {field_value}\n"

        return formatted_info

    except PanosError as e:
        logger.error(
            "Failed to retrieve system information",
            error=str(e),
            error_type=e.__class__.__name__,
            details=getattr(e, "details", {}),
            context=ctx,
        )
        return format_error_response(e)
    except Exception as e:
        logger.error(
            "Unexpected error while retrieving system information",
            error=str(e),
            context=ctx,
        )
        return format_error_response(e)


@mcp.tool()
async def retrieve_address_objects(ctx: Context) -> str:
    """Get address objects configured on the Palo Alto Networks firewall.

    Args:
        ctx: The MCP context object for request-specific logging

    Returns:
        A formatted string containing address object information.

    Raises:
        PanosConnectionError: If connection to the firewall fails
        PanosAuthenticationError: If authentication fails
        PanosOperationError: If the operation fails
    """
    logger.info("Retrieving address objects", context=ctx)

    try:
        settings = get_settings()
        async with PanosApiClient(settings) as client:
            address_objects_dict = await client.get_address_objects()

        if not address_objects_dict:
            return "No address objects found on the firewall."

        # Validate and convert all objects using our model
        address_objects = [AddressObject(**obj) for obj in address_objects_dict]

        # Format the address objects as a readable string
        formatted_output = "# Palo Alto Networks Firewall Address Objects\n\n"

        # Group address objects by location for better organization
        objects_by_location: dict[str, list[AddressObject]] = {}
        for obj in address_objects:
            if obj.location not in objects_by_location:
                objects_by_location[obj.location] = []
            objects_by_location[obj.location].append(obj)

        # Display objects grouped by location
        for location, objects in objects_by_location.items():
            formatted_output += f"## {location.capitalize()} Address Objects\n\n"

            for obj in objects:
                formatted_output += f"### {obj.name}\n"
                formatted_output += f"- **Type**: {obj.type}\n"
                formatted_output += f"- **Value**: {obj.value}\n"

                if obj.description:
                    formatted_output += f"- **Description**: {obj.description}\n"

                if obj.tags:
                    formatted_output += f"- **Tags**: {', '.join(obj.tags)}\n"

                formatted_output += "\n"

        return formatted_output

    except PanosError as e:
        logger.error(
            "Failed to retrieve address objects",
            error=str(e),
            error_type=e.__class__.__name__,
            details=getattr(e, "details", {}),
            context=ctx,
        )
        return format_error_response(e)
    except Exception as e:
        logger.error(
            "Unexpected error while retrieving address objects",
            error=str(e),
            context=ctx,
        )
        return format_error_response(e)


@mcp.tool()
async def retrieve_security_zones(ctx: Context) -> str:
    """Get security zones configured on the Palo Alto Networks firewall.

    Args:
        ctx: The MCP context object for request-specific logging

    Returns:
        A formatted string containing security zone information.

    Raises:
        PanosConnectionError: If connection to the firewall fails
        PanosAuthenticationError: If authentication fails
        PanosOperationError: If the operation fails
    """
    logger.info("Retrieving security zones", context=ctx)

    try:
        settings = get_settings()
        async with PanosApiClient(settings) as client:
            security_zones_dict = await client.get_security_zones()

        if not security_zones_dict:
            return "No security zones found on the firewall."

        # Validate and convert all zones using our model
        security_zones = [SecurityZone(**zone) for zone in security_zones_dict]

        # Format the security zones as a readable string
        formatted_output = "# Palo Alto Networks Firewall Security Zones\n\n"

        # Group zones by location for better organization
        zones_by_location: dict[str, list[SecurityZone]] = {}
        for zone in security_zones:
            if zone.location not in zones_by_location:
                zones_by_location[zone.location] = []
            zones_by_location[zone.location].append(zone)

        # Display zones grouped by location
        for location, zones in zones_by_location.items():
            formatted_output += f"## {location.capitalize()} Security Zones\n\n"

            for zone in zones:
                formatted_output += f"### {zone.name}\n"
                formatted_output += f"- **Type**: {zone.type}\n"

                if zone.interfaces:
                    formatted_output += (
                        f"- **Interfaces**: {', '.join(zone.interfaces)}\n"
                    )

                formatted_output += f"- **User Identification**: {'Enabled' if zone.user_identification else 'Disabled'}\n"
                formatted_output += f"- **Device Identification**: {'Enabled' if zone.device_identification else 'Disabled'}\n"
                formatted_output += f"- **Packet Buffer Protection**: {'Enabled' if zone.packet_buffer_protection else 'Disabled'}\n"

                formatted_output += "\n"

        return formatted_output

    except PanosError as e:
        logger.error(
            "Failed to retrieve security zones",
            error=str(e),
            error_type=e.__class__.__name__,
            details=getattr(e, "details", {}),
            context=ctx,
        )
        return format_error_response(e)
    except Exception as e:
        logger.error(
            "Unexpected error while retrieving security zones",
            error=str(e),
            context=ctx,
        )
        return format_error_response(e)


async def shutdown() -> None:
    """Perform any necessary cleanup before shutting down."""
    logger.info("Shutting down MCP server")


def main() -> None:
    """Run the MCP server."""
    import asyncio
    import sys

    from mcp import run

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    run(mcp, shutdown_handler=shutdown)


if __name__ == "__main__":
    main()
