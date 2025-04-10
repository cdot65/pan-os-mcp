# PAN-OS API Client Module

The PAN-OS API client module (`pan_os_api.py`) is responsible for making requests to the Palo Alto Networks XML API and parsing the responses.

## PanosApiClient Class

```python
class PanosApiClient:
    """Client for interacting with the Palo Alto Networks XML API.

    This class provides methods for retrieving data from a Palo Alto Networks
    Next-Generation Firewall (NGFW) or Panorama through its XML API.

    Attributes:
        hostname: The hostname or IP address of the NGFW or Panorama.
        api_key: The API key for authenticating with the NGFW or Panorama.
        client: An httpx AsyncClient for making HTTP requests.
    """
```

### Initialization

```python
def __init__(self, settings: Settings) -> None:
    """Initialize the PanosApiClient.

    Args:
        settings: Application settings containing NGFW connection information.
    """
    self.hostname = settings.panos_hostname
    self.api_key = settings.panos_api_key
    self.base_url = f"https://{self.hostname}/api/"
    self.client = httpx.AsyncClient(verify=False)  # In production, use proper cert verification
```

### Async Context Manager Support

The client implements the async context manager protocol, allowing it to be used with the `async with` statement:

```python
async def __aenter__(self) -> "PanosApiClient":
    """Async context manager entry.

    Returns:
        The PanosApiClient instance.
    """
    return self

async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: object,
) -> None:
    """Async context manager exit.

    Args:
        exc_type: The exception type, if an exception was raised.
        exc_val: The exception value, if an exception was raised.
        exc_tb: The exception traceback, if an exception was raised.
    """
    await self.client.aclose()
```

### Making Requests

```python
async def _make_request(self, params: dict[str, str]) -> ElementTree.Element:
    """Make a request to the Palo Alto Networks XML API.

    Args:
        params: Dictionary of query parameters to include in the request.

    Returns:
        The XML response as an ElementTree Element.

    Raises:
        httpx.HTTPError: If the HTTP request fails.
        ValueError: If the API returns an error response.
    """
    # Add the API key to the parameters
    params["key"] = self.api_key

    try:
        # Make the request
        response = await self.client.get(self.base_url, params=params)
        response.raise_for_status()

        # Parse the XML response
        root = ElementTree.fromstring(response.text)

        # Check for API errors
        status = root.find(".//status")
        if status is not None and status.text != "success":
            error_msg = root.find(".//msg")
            if error_msg is not None and error_msg.text:
                raise ValueError(f"API error: {error_msg.text}")
            else:
                raise ValueError("Unknown API error")

        return root
    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"HTTP request failed: {str(e)}")
```

## API Methods

### get_system_info

```python
async def get_system_info(self) -> dict[str, str]:
    """Get system information from the firewall.

    Returns:
        Dictionary containing system information.
    """
    params = {"type": "op", "cmd": "<show><s><info></info></s></show>"}

    root = await self._make_request(params)
    result = root.find(".//result")

    if result is None:
        raise ValueError("No system information found in response")

    # Extract system information
    system_info = {}
    for child in result:
        if child.text is not None:
            system_info[child.tag] = child.text
        else:
            system_info[child.tag] = ""

    return system_info
```

This method retrieves system information from the firewall, including hostname, model, serial number, software version, and uptime.

### get_address_objects

```python
async def get_address_objects(self) -> list[dict[str, str]]:
    """Get address objects configured on the firewall or Panorama.

    Returns:
        List of dictionaries containing address object information.
    """
    # First, check if this is a Panorama by trying to get device groups
    is_panorama = False
    device_groups = []
    
    try:
        # Try to get device groups (only works on Panorama)
        dg_params = {
            "type": "config",
            "action": "get",
            "xpath": "/config/devices/entry/device-group",
        }
        dg_root = await self._make_request(dg_params)
        dg_entries = dg_root.findall(".//entry")
        
        if dg_entries:
            is_panorama = True
            device_groups = [entry.get("name") for entry in dg_entries if entry.get("name")]
            logger.info(f"Detected Panorama with {len(device_groups)} device groups")
    except Exception as e:
        logger.warning(f"Failed to check for device groups, assuming firewall: {str(e)}")
    
    address_objects = []
    
    if is_panorama:
        # Process device groups for Panorama
        for dg_name in device_groups:
            if not dg_name:
                continue
                
            # Get addresses for this device group
            dg_addr_params = {
                "type": "config",
                "action": "get",
                "xpath": f"/config/devices/entry/device-group/entry[@name='{dg_name}']/address",
            }
            
            dg_addr_root = await self._make_request(dg_addr_params)
            dg_entries = dg_addr_root.findall(".//entry")
            
            # Process each address object in the device group
            for entry in dg_entries:
                address_obj = {"name": entry.get("name") or "", "location": f"device-group:{dg_name}"}
                
                # Process the address object types and values
                ip_netmask = entry.find("ip-netmask")
                if ip_netmask is not None and ip_netmask.text is not None:
                    address_obj["type"] = "ip-netmask"
                    address_obj["value"] = ip_netmask.text
                elif (ip_range := entry.find("ip-range")) is not None and ip_range.text is not None:
                    address_obj["type"] = "ip-range"
                    address_obj["value"] = ip_range.text
                elif (fqdn := entry.find("fqdn")) is not None and fqdn.text is not None:
                    address_obj["type"] = "fqdn"
                    address_obj["value"] = fqdn.text
                else:
                    address_obj["type"] = "unknown"
                    address_obj["value"] = ""
                
                # Get description if available
                description = entry.find("description")
                if description is not None and description.text is not None:
                    address_obj["description"] = description.text
                
                address_objects.append(address_obj)
    
    # Always check for vsys address objects (works for both firewall and Panorama)
    vsys_params = {
        "type": "config",
        "action": "get",
        "xpath": "/config/devices/entry/vsys/entry/address",
    }
    
    vsys_root = await self._make_request(vsys_params)
    vsys_entries = vsys_root.findall(".//entry")
    
    # Process each address object in vsys
    for entry in vsys_entries:
        address_obj = {"name": entry.get("name") or "", "location": "vsys"}
        
        # Process the address object types and values
        ip_netmask = entry.find("ip-netmask")
        if ip_netmask is not None and ip_netmask.text is not None:
            address_obj["type"] = "ip-netmask"
            address_obj["value"] = ip_netmask.text
        elif (ip_range := entry.find("ip-range")) is not None and ip_range.text is not None:
            address_obj["type"] = "ip-range"
            address_obj["value"] = ip_range.text
        elif (fqdn := entry.find("fqdn")) is not None and fqdn.text is not None:
            address_obj["type"] = "fqdn"
            address_obj["value"] = fqdn.text
        else:
            address_obj["type"] = "unknown"
            address_obj["value"] = ""
        
        # Get description if available
        description = entry.find("description")
        if description is not None and description.text is not None:
            address_obj["description"] = description.text
        
        address_objects.append(address_obj)
    
    return address_objects
```

This method retrieves address objects configured on the firewall or Panorama, including their names, types, values, descriptions, and locations (device group or vsys).

### get_security_zones

```python
async def get_security_zones(self) -> list[dict[str, str]]:
    """Get security zones configured on the firewall.

    Returns:
        List of dictionaries containing security zone information.
    """
    params = {"type": "config", "action": "get", "xpath": "/config/devices/entry/vsys/entry/zone"}

    root = await self._make_request(params)
    entries = root.findall(".//entry")

    zones = []
    for entry in entries:
        zone = {"name": entry.get("name") or ""}

        # Get zone type
        if entry.find("network/layer3") is not None:
            zone["type"] = "layer3"
            interfaces = entry.findall(".//member")
            zone["interfaces"] = ",".join([interface.text for interface in interfaces if interface.text])
        elif entry.find("network/layer2") is not None:
            zone["type"] = "layer2"
            interfaces = entry.findall(".//member")
            zone["interfaces"] = ",".join([interface.text for interface in interfaces if interface.text])
        elif entry.find("network/virtual-wire") is not None:
            zone["type"] = "virtual-wire"
            interfaces = entry.findall(".//member")
            zone["interfaces"] = ",".join([interface.text for interface in interfaces if interface.text])
        elif entry.find("network/tap") is not None:
            zone["type"] = "tap"
            interfaces = entry.findall(".//member")
            zone["interfaces"] = ",".join([interface.text for interface in interfaces if interface.text])
        elif entry.find("network/external") is not None:
            zone["type"] = "external"
            zone["interfaces"] = ""
        else:
            zone["type"] = "unknown"
            zone["interfaces"] = ""

        zones.append(zone)

    return zones
```

This method retrieves security zones configured on the firewall, including their names, types, and interfaces.

### get_security_policies

```python
async def get_security_policies(self) -> list[dict[str, str | list[str]]]:
    """Get security policies configured on the firewall.

    Returns:
        List of dictionaries containing security policy information.
    """
    params = {"type": "config", "action": "get", "xpath": "/config/devices/entry/vsys/entry/rulebase/security/rules"}

    root = await self._make_request(params)
    entries = root.findall(".//entry")

    policies = []
    for entry in entries:
        policy = {"name": entry.get("name") or ""}

        # Source information
        source_zones = entry.findall(".//from/member")
        policy["source_zones"] = ",".join([zone.text for zone in source_zones if zone.text])

        source_addresses = entry.findall(".//source/member")
        policy["source_addresses"] = ",".join([addr.text for addr in source_addresses if addr.text])

        # Destination information
        dest_zones = entry.findall(".//to/member")
        policy["destination_zones"] = ",".join([zone.text for zone in dest_zones if zone.text])

        dest_addresses = entry.findall(".//destination/member")
        policy["destination_addresses"] = ",".join([addr.text for addr in dest_addresses if addr.text])

        # Application and service information
        applications = entry.findall(".//application/member")
        policy["applications"] = ",".join([app.text for app in applications if app.text])

        services = entry.findall(".//service/member")
        policy["services"] = ",".join([svc.text for svc in services if svc.text])

        # Action
        action = entry.find("action")
        if action is not None and action.text is not None:
            policy["action"] = action.text
        else:
            policy["action"] = ""

        # Description
        description = entry.find("description")
        if description is not None and description.text is not None:
            policy["description"] = description.text
        else:
            policy["description"] = ""

        policies.append(policy)

    return policies
```

This method retrieves security policies configured on the firewall, including their names, sources, destinations, applications, and actions.

## XML Parsing

The module uses Python's standard `xml.etree.ElementTree` module to parse XML responses from the Palo Alto Networks API. Each method includes specific parsing logic to extract the relevant data from the XML structure and convert it to a more usable Python data structure (dictionaries and lists).
