# PAN-OS MCP Server

A Model Context Protocol (MCP) server for interacting with Palo Alto Networks firewalls. This server provides tools for retrieving and managing firewall configurations using the PAN-OS XML API.

## Features

- **System Information**: Retrieve firewall system details
- **Address Objects**: List and inspect address objects
- **Security Zones**: View security zone configurations
- **Security Policies**: Examine security policy rules
- **Health Check**: Monitor server and firewall connectivity status

## Installation

### Prerequisites

- Python 3.10 or later
- Access to a Palo Alto Networks firewall
- PAN-OS API key

### Using pip

```bash
pip install .
```

### Using uv (recommended)

```bash
uv pip install .
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your firewall details:
   ```bash
   # Hostname or IP address of your Palo Alto Networks firewall
   PANOS_HOSTNAME=firewall.example.com

   # API key for authenticating with the firewall
   # Generate this in the firewall web interface:
   # Device > Users > API Key Generation
   PANOS_API_KEY=your-api-key-here

   # Enable debug logging (optional)
   PANOS_DEBUG=false
   ```

## Usage

### Running the Server

```bash
python -m palo_alto_mcp
```

### Available Tools

#### check_health
Check server and firewall connectivity status.
```python
result = await client.check_health()
```

#### show_system_info
Retrieve firewall system information.
```python
result = await client.show_system_info()
```

#### retrieve_address_objects
List configured address objects.
```python
result = await client.retrieve_address_objects()
```

#### retrieve_security_zones
View security zone configurations.
```python
result = await client.retrieve_security_zones()
```

#### retrieve_security_policies
Examine security policy rules.
```python
result = await client.retrieve_security_policies()
```

## Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pan-os-mcp
   ```

2. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=palo_alto_mcp

# Run specific test file
pytest tests/test_server.py
```

### Code Style

This project uses:
- `ruff` for linting
- `black` for code formatting
- `pyright` for type checking

Run formatters and linters:
```bash
# Format code
black src tests

# Run linters
ruff check src tests
pyright src tests
```

## Error Handling

The server uses custom exceptions for different error scenarios:

- `PanosConnectionError`: Connection issues with the firewall
- `PanosAuthenticationError`: API key or authentication problems
- `PanosConfigurationError`: Invalid configuration
- `PanosOperationError`: Failed operations

## Logging

The server uses structured logging via MCP's logging utilities. Debug logging can be enabled by setting `PANOS_DEBUG=true` in your environment.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

[Insert your license information here]
