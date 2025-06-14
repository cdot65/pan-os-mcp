"""Palo Alto Networks MCP Server implementation using FastMCP."""

import logging

from mcp.server.fastmcp import Context, FastMCP

from palo_alto_mcp.config import get_settings
from palo_alto_mcp.pan_os_api import PanOSAPIClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastMCP instance
mcp = FastMCP("PaloAltoMCPServer")


@mcp.tool()
async def show_system_info(ctx: Context) -> str:  # noqa: ARG001
    """Get system information from the Palo Alto Networks firewall.

    Returns:
        A formatted string containing system information.

    """
    logger.info("Retrieving system information")

    try:
        settings = get_settings()
        logger.info(
            f"Loaded PANOS_HOSTNAME={settings.panos_hostname}, PANOS_API_KEY={'set' if settings.panos_api_key else 'unset'}"
        )
        async with PanOSAPIClient(settings) as client:
            system_info = await client.get_system_info()

        # Format the system information as a readable string
        formatted_info = "# Palo Alto Networks Firewall System Information\n\n"
        for key, value in system_info.items():
            formatted_info += f"**{key}**: {value}\n"

        return formatted_info
    except Exception as e:
        error_msg = f"Error retrieving system information: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def retrieve_address_objects(ctx: Context) -> str:  # noqa: ARG001
    """Get address objects configured on the Palo Alto Networks firewall.

    Returns:
        A formatted string containing address object information.

    """
    logger.info("Retrieving address objects")

    try:
        settings = get_settings()
        async with PanOSAPIClient(settings) as client:
            address_objects = await client.get_address_objects()

        if not address_objects:
            return "No address objects found on the firewall."

        # Format the address objects as a readable string
        formatted_output = "# Palo Alto Networks Firewall Address Objects\n\n"

        # Group address objects by location for better organization
        objects_by_location: dict[str, list[dict[str, str]]] = {}
        for obj in address_objects:
            location = obj.get("location", "Unknown")
            if location not in objects_by_location:
                objects_by_location[location] = []
            objects_by_location[location].append(obj)

        # Display objects grouped by location
        for location, objects in objects_by_location.items():
            formatted_output += f"## {location.capitalize()} Address Objects\n\n"

            for obj in objects:
                formatted_output += f"### {obj['name']}\n"
                formatted_output += f"- **Type**: {obj.get('type', 'N/A')}\n"
                formatted_output += f"- **Value**: {obj.get('value', 'N/A')}\n"

                if "description" in obj:
                    formatted_output += f"- **Description**: {obj['description']}\n"

                if "tags" in obj:
                    formatted_output += f"- **Tags**: {obj['tags']}\n"

                formatted_output += "\n"

        return formatted_output
    except Exception as e:
        error_msg = f"Error retrieving address objects: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def retrieve_security_zones(ctx: Context) -> str:  # noqa: ARG001
    """Get security zones configured on the Palo Alto Networks firewall.

    Returns:
        A formatted string containing security zone information.

    """
    logger.info("Retrieving security zones")

    try:
        settings = get_settings()
        async with PanOSAPIClient(settings) as client:
            zones = await client.get_security_zones()

        if not zones:
            return "No security zones found on the firewall."

        # Format the security zones as a readable string
        formatted_output = "# Palo Alto Networks Firewall Security Zones\n\n"
        for zone in zones:
            formatted_output += f"## {zone['name']}\n"
            formatted_output += f"- **Type**: {zone.get('type', 'N/A')}\n"

            if "interfaces" in zone and zone["interfaces"]:
                formatted_output += "- **Interfaces**:\n"
                for interface in zone["interfaces"].split(","):
                    if interface:
                        formatted_output += f"  - {interface}\n"
            else:
                formatted_output += "- **Interfaces**: None\n"

            formatted_output += "\n"

        return formatted_output
    except Exception as e:
        error_msg = f"Error retrieving security zones: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
async def retrieve_security_policies(ctx: Context) -> str:  # noqa: ARG001
    """Get security policies configured on the Palo Alto Networks firewall.

    Returns:
        A formatted string containing security policy information.

    """
    logger.info("Retrieving security policies")

    try:
        settings = get_settings()
        async with PanOSAPIClient(settings) as client:
            policies = await client.get_security_policies()

        if not policies:
            return "No security policies found on the firewall."

        # Format the security policies as a readable string
        formatted_output = "# Palo Alto Networks Firewall Security Policies\n\n"
        for policy in policies:
            formatted_output += f"## {policy['name']}\n"

            if "description" in policy and policy["description"]:
                formatted_output += f"- **Description**: {policy['description']}\n"

            formatted_output += f"- **Action**: {policy.get('action', 'N/A')}\n"

            formatted_output += "- **Source Zones**:\n"
            for zone in policy.get("source_zones", "").split(","):
                if zone:
                    formatted_output += f"  - {zone}\n"

            formatted_output += "- **Source Addresses**:\n"
            for addr in policy.get("source_addresses", "").split(","):
                if addr:
                    formatted_output += f"  - {addr}\n"

            formatted_output += "- **Destination Zones**:\n"
            for zone in policy.get("destination_zones", "").split(","):
                if zone:
                    formatted_output += f"  - {zone}\n"

            formatted_output += "- **Destination Addresses**:\n"
            for addr in policy.get("destination_addresses", "").split(","):
                if addr:
                    formatted_output += f"  - {addr}\n"

            formatted_output += "- **Applications**:\n"
            for app in policy.get("applications", "").split(","):
                if app:
                    formatted_output += f"  - {app}\n"

            formatted_output += "- **Services**:\n"
            for svc in policy.get("services", "").split(","):
                if svc:
                    formatted_output += f"  - {svc}\n"

            formatted_output += "\n"

        return formatted_output
    except Exception as e:
        error_msg = f"Error retrieving security policies: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


def main() -> None:
    """
    Run the MCP server as a network server with SSE endpoints.
    Exposes /sse and /messages/ endpoints for Windsurf and MCP clients.
    """
    get_settings()
    logger.info("Starting Palo Alto Networks MCP Server")
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
