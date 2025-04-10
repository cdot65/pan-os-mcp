# Mermaid Diagram Examples

This page contains examples of diagrams and charts that can be created using mermaid for the PAN-OS MCP Server documentation.

## Architecture Diagrams

### MCP Server Architecture

```mermaid
graph TB
    client[MCP Client] --- server[FastMCP Server]
    server --- panos[Palo Alto NGFW]
    
    subgraph "PAN-OS MCP Server"
        server
        api[PAN-OS API Client]
        config[Configuration]
        server --- api
        server --- config
        api --- panos
    end
```

### Communication Flow

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant API
    participant NGFW
    
    Client->>Server: Request tool execution
    Server->>API: Call PAN-OS API
    API->>NGFW: Send XML API request
    NGFW-->>API: Return XML response
    API-->>Server: Return parsed data
    Server-->>Client: Return formatted result
```

## Deployment Diagrams

### Standard Deployment

```mermaid
graph LR
    user[User] --> cli[CLI Command]
    cli --> server[MCP Server]
    server --- ngfw[PAN-OS NGFW]
```

### Container Deployment

```mermaid
graph TB
    subgraph host[Host Machine]
        docker[Docker Container]
        
        subgraph docker
            server[MCP Server]
        end
    end
    
    client[MCP Client] --- server
    server --- ngfw[Palo Alto NGFW]
```

## Process Flows

### Tool Registration Process

```mermaid
graph TD
    A[Start] --> B[Define function]
    B --> C[Add @mcp.tool]
    C --> D[Define parameters]
    D --> E[Implement function]
    E --> F[End]
```

### API Request Handling

```mermaid
sequenceDiagram
    participant Tool
    participant API
    participant NGFW
    
    Tool->>API: Call API method
    API->>NGFW: Send XML request
    NGFW-->>API: Return response
    API-->>Tool: Return data
```

## State Diagrams

### MCP Server Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Initializing
    Initializing --> Running: Valid config
    Initializing --> Failed: Invalid config
    Running --> Shutdown: Termination signal
    Shutdown --> [*]
    Failed --> [*]
```

### API Request States

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> InProgress
    InProgress --> Success
    InProgress --> Failed
    Success --> [*]
    Failed --> [*]
```

## Class Diagrams

### MCP Server Components

```mermaid
classDiagram
    class FastMCP {
        +run()
        +tool()
    }
    
    class PanosApiClient {
        +get_system_info()
        +get_address_objects()
    }
    
    class Settings {
        +PANOS_HOSTNAME
        +PANOS_API_KEY
    }
    
    FastMCP --> PanosApiClient
    FastMCP --> Settings
```
