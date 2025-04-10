# Server Module

The server module (`server.py`) is the core of the Palo Alto Networks MCP Server. It creates an instance of `FastMCP` from the `modelcontextprotocol` SDK and defines the tool functions that can be called by MCP clients.

## FastMCP Instance

```python
from mcp.server.fastmcp import Context, FastMCP
from palo_alto_mcp.config import get_settings
from palo_alto_mcp.pan_os_api import PanosApiClient

# Create FastMCP instance
mcp = FastMCP("PaloAltoMCPServer")
```

## Tool Functions

### show_system_info

```python
@mcp.tool()
async def show_system_info(ctx: Context) -> str:  # noqa: ARG001
    """Get system information from the Palo Alto Networks firewall.

    Returns:
        A formatted string containing system information.
    """
    # Implementation details...
```

This tool retrieves system information from the Palo Alto Networks firewall, including hostname, model, serial number, software version, and uptime.

### retrieve_address_objects

```python
@mcp.tool()
async def retrieve_address_objects(ctx: Context) -> str:  # noqa: ARG001
    """Get address objects configured on the Palo Alto Networks firewall.

    Returns:
        A formatted string containing address object information.
    """
    # Implementation details...
```

This tool retrieves address objects configured on the Palo Alto Networks firewall or Panorama, including their names, types, values, and descriptions. When connected to a Panorama device, it will organize address objects by device group, providing a hierarchical view of the configuration.

### retrieve_security_zones

```python
@mcp.tool()
async def retrieve_security_zones(ctx: Context) -> str:  # noqa: ARG001
    """Get security zones configured on the Palo Alto Networks firewall.

    Returns:
        A formatted string containing security zone information.
    """
    # Implementation details...
```

This tool retrieves security zones configured on the Palo Alto Networks firewall, including their names, types, and interfaces.

### retrieve_security_policies

```python
@mcp.tool()
async def retrieve_security_policies(ctx: Context) -> str:  # noqa: ARG001
    """Get security policies configured on the Palo Alto Networks firewall.

    Returns:
        A formatted string containing security policy information.
    """
    # Implementation details...
```

This tool retrieves security policies configured on the Palo Alto Networks firewall, including their names, sources, destinations, applications, and actions.

## Implementation Details

Each tool function follows a similar pattern:

1. Log the start of the operation
2. Get the application settings
3. Create an instance of the PAN-OS API client
4. Call the appropriate method on the API client
5. Format the result as a Markdown string
6. Return the formatted result
7. Handle any exceptions and return an error message

For example, the implementation of `retrieve_address_objects` looks like this:

```python
@mcp.tool()
async def retrieve_address_objects(ctx: Context) -> str:  # noqa: ARG001
    logger.info("Retrieving address objects")

    try:
        settings = get_settings()
        async with PanosApiClient(settings) as client:
            address_objects = await client.get_address_objects()

        if not address_objects:
            return "No address objects found on the firewall."

        # Format the address objects as a readable string
        formatted_output = "# Palo Alto Networks Firewall Address Objects\n\n"
        
        # Group address objects by location (device group or vsys)
        objects_by_location = {}
        for obj in address_objects:
            location = obj.get('location', 'unknown')
            if location not in objects_by_location:
                objects_by_location[location] = []
            objects_by_location[location].append(obj)
        
        # Output address objects grouped by location
        for location, objects in objects_by_location.items():
            formatted_output += f"## {location} Address Objects\n\n"
            for obj in objects:
                formatted_output += f"### {obj['name']}\n"
                formatted_output += f"- **Type**: {obj.get('type', 'N/A')}\n"
                formatted_output += f"- **Value**: {obj.get('value', 'N/A')}\n"
                if 'description' in obj:
                    formatted_output += f"- **Description**: {obj['description']}\n"
                formatted_output += "\n"

        return formatted_output
    except Exception as e:
        error_msg = f"Error retrieving address objects: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
```

## Main Function

```python
def main() -> None:
    """Run the MCP server."""
    try:
        # Validate settings on startup
        get_settings()

        # Start the server
        logger.info("Starting Palo Alto Networks MCP Server")
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
```

The `main()` function is the entry point for the server. It validates the settings, starts the server, and handles any exceptions that occur during startup.

## Error Handling

All tool functions include comprehensive error handling to ensure that any issues with the Palo Alto Networks API are properly reported to the client. Errors are logged and returned as formatted strings, making them easy to understand and troubleshoot.

## Logging

The server uses Python's standard logging module to provide informational and error messages. The log level can be controlled via the `PANOS_DEBUG` environment variable.
