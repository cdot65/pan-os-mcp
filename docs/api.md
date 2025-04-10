# PAN-OS MCP Server API Documentation

## Overview

The PAN-OS MCP Server exposes a set of tools for interacting with Palo Alto Networks firewalls through the Model Context Protocol (MCP). Each tool is implemented as an async function decorated with `@mcp.tool()`.

## Available Tools

### 1. Check Health (`check_health`)

Verifies the health and connectivity of the MCP server and PAN-OS firewall.

**Input:**
- `ctx`: MCP Context object

**Output Format:**
```markdown
# PAN-OS MCP Server Health Check

- **MCP Server Version**: 0.1.0
- **Target Firewall**: firewall.example.com
- **Debug Mode**: Disabled

## Firewall Information
- **Hostname**: fw01.example.com
- **Model**: PA-VM
- **PAN-OS Version**: 10.2.3
- **Uptime**: 7 days
- **Connection Status**: Connected
- **GlobalProtect Version**: 6.0.0 (if applicable)
```

**Error Response:**
```markdown
# PAN-OS MCP Server Health Check

- **MCP Server Version**: 0.1.0
- **Target Firewall**: firewall.example.com
- **Debug Mode**: Disabled

## Connection Status
- **Status**: Failed
- **Error**: Connection refused
```

### 2. System Information (`show_system_info`)

Retrieves detailed system information from the firewall.

**Input:**
- `ctx`: MCP Context object

**Output Format:**
```markdown
# Palo Alto Networks Firewall System Information

**Hostname**: fw01.example.com
**IP Address**: 192.168.1.1
**Netmask**: 255.255.255.0
**Default Gateway**: 192.168.1.254
**MAC Address**: 00:1A:2B:3C:4D:5E
**Time**: 2024-03-14 12:00:00
**Uptime**: 7 days
**Version**: 10.2.3
**GlobalProtect Version**: 6.0.0
```

### 3. Address Objects (`retrieve_address_objects`)

Retrieves configured address objects from the firewall.

**Input:**
- `ctx`: MCP Context object

**Output Format:**
```markdown
# Palo Alto Networks Firewall Address Objects

## Shared Address Objects

### web-server
- **Type**: ip-netmask
- **Value**: 192.168.1.100/32
- **Description**: Primary web server
- **Tags**: web, production

### internal-subnet
- **Type**: ip-netmask
- **Value**: 192.168.0.0/16
- **Description**: Internal network
- **Tags**: internal

## Device Group: Branch-Office Address Objects

### branch-server
- **Type**: fqdn
- **Value**: branch.example.com
- **Description**: Branch office server
- **Tags**: branch, server
```

### 4. Security Zones (`retrieve_security_zones`)

Retrieves configured security zones from the firewall.

**Input:**
- `ctx`: MCP Context object

**Output Format:**
```markdown
# Palo Alto Networks Firewall Security Zones

## Vsys1 Security Zones

### trust
- **Type**: layer3
- **Interfaces**: ethernet1/1, ethernet1/2
- **User Identification**: Enabled
- **Device Identification**: Disabled
- **Packet Buffer Protection**: Enabled

### untrust
- **Type**: layer3
- **Interfaces**: ethernet1/3
- **User Identification**: Disabled
- **Device Identification**: Disabled
- **Packet Buffer Protection**: Enabled
```

## Error Handling

All tools use a consistent error handling approach:

1. **PAN-OS Specific Errors:**
```markdown
Error (PanosConnectionError): Failed to connect to firewall

Details:
- host: firewall.example.com
- port: 443
- timeout: 30s
```

2. **Generic Errors:**
```markdown
Error: An unexpected error occurred: <error message>
```

## Data Models

### SystemInfo
```python
class SystemInfo(BaseModel):
    hostname: str
    ip_address: str
    netmask: str
    default_gateway: str
    mac_address: str
    time: str
    uptime: str
    version: str
    gp_version: str | None
```

### AddressObject
```python
class AddressObject(BaseModel):
    name: str
    type: Literal["ip-netmask", "ip-range", "fqdn"]
    value: str
    description: str | None
    location: str = "vsys1"
    tags: list[str] | None = []
```

### SecurityZone
```python
class SecurityZone(BaseModel):
    name: str
    type: Literal["layer3", "layer2", "virtual-wire", "tap"]
    location: str = "vsys1"
    interfaces: list[str] | None = []
    user_identification: bool = False
    device_identification: bool = False
    packet_buffer_protection: bool = False
```

## Configuration

### Environment Variables

| Variable         | Description                | Required | Default |
| ---------------- | -------------------------- | -------- | ------- |
| `PANOS_HOSTNAME` | Firewall hostname/IP       | Yes      | -       |
| `PANOS_API_KEY`  | API key for authentication | Yes      | -       |
| `DEBUG`          | Enable debug logging       | No       | False   |

## Logging

### Log Levels

- **DEBUG**: API request/response details
- **INFO**: Operation status and timing
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures
- **CRITICAL**: System-level failures

### Log Format

```json
{
    "timestamp": "2024-03-14T12:00:00.000Z",
    "level": "INFO",
    "event": "Retrieving address objects",
    "context": {
        "request_id": "abc123",
        "operation": "get_address_objects",
        "target": "firewall.example.com"
    },
    "duration_ms": 150
}
```

## Performance Considerations

1. **Connection Management**
   - Uses async HTTP client
   - Implements connection pooling
   - Automatic connection cleanup

2. **Response Processing**
   - Streaming XML parsing
   - Memory-efficient data structures
   - Lazy evaluation where possible

3. **Error Recovery**
   - Automatic reconnection
   - Request retries
   - Circuit breaker pattern

## Security Considerations

1. **Authentication**
   - API key-based authentication
   - Environment variable configuration
   - No hardcoded credentials

2. **Communication**
   - HTTPS encryption
   - Certificate validation
   - Secure error handling

3. **Input Validation**
   - Pydantic model validation
   - Type checking
   - XML response validation 