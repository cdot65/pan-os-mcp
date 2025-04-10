# PAN-OS MCP Server

Welcome to the PAN-OS Model Context Protocol (MCP) Server documentation. This server provides a set of tools for interacting with Palo Alto Networks firewalls through the Model Context Protocol.

## Overview

The PAN-OS MCP Server is designed to provide seamless integration between Palo Alto Networks firewalls and MCP-enabled applications. It offers a set of tools for retrieving and managing firewall configurations, monitoring system status, and automating common tasks.

## Key Features

- **System Information**: Retrieve detailed system information from your firewall
- **Address Objects**: Manage and view address objects configuration
- **Security Zones**: Access and monitor security zone settings
- **Health Checks**: Verify connectivity and system status
- **Async Operations**: All operations are asynchronous for better performance
- **Type Safety**: Full type checking and validation using Pydantic
- **Error Handling**: Comprehensive error handling and reporting

## Quick Links

- [Architecture Overview](architecture.md)
- [API Reference](api.md)
- [Future Improvements](improvements.md)

## Getting Started

### Prerequisites

- Python 3.10 or later
- Access to a Palo Alto Networks firewall
- PAN-OS API key

### Installation

```bash
pip install pan-os-mcp
```

### Basic Usage

1. Set up your environment variables:
```bash
export PANOS_HOSTNAME="your-firewall.example.com"
export PANOS_API_KEY="your-api-key"
```

2. Start using the MCP tools:
```python
from palo_alto_mcp.server import create_server

server = create_server()
await server.start()
```

## Documentation Structure

- **Architecture**: Detailed system design and component interactions
- **API Reference**: Complete documentation of available tools and their usage
- **Improvements**: Planned enhancements and future development

## Contributing

We welcome contributions! Please see our [contributing guidelines](contributing.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/cdot65/pan-os-mcp/blob/main/LICENSE) file for details.
