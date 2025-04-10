"""PAN-OS XML API client implementation."""

import logging
from typing import Any, TypeVar
from xml.etree import ElementTree

import httpx

from palo_alto_mcp.config import Settings
from palo_alto_mcp.models import (
    AddressObject,
    PanosError,
    PanosOperationError,
    SystemInfo,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PanosApiClient:
    """Client for interacting with the Palo Alto Networks XML API.

    This class provides methods for retrieving data from a Palo Alto Networks
    Next-Generation Firewall (NGFW) through its XML API.

    Attributes:
        hostname: The hostname or IP address of the NGFW.
        api_key: The API key for authenticating with the NGFW.
        client: An httpx AsyncClient for making HTTP requests.

    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the PanosApiClient.

        Args:
            settings: Application settings containing NGFW connection information.

        """
        self.hostname = settings.panos_hostname
        self.api_key = settings.panos_api_key
        self.base_url = f"https://{self.hostname}/api/"
        self.client = httpx.AsyncClient(verify=False)  # In production, use proper cert verification

    async def __aenter__(self) -> "PanosApiClient":
        """Enter the async context manager.

        Returns:
            The client instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: ElementTree.Element | None,
    ) -> None:
        """Exit the async context manager.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

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
            logger.debug(f"Making API request to {self.base_url} with params: {params}")
            response = await self.client.get(self.base_url, params=params, timeout=30.0)
            response.raise_for_status()

            # Parse the XML response
            response_text = response.text
            if not response_text:
                raise ValueError("Empty response from API")

            logger.debug(f"Received response: {response_text[:200]}..." if len(response_text) > 200 else response_text)

            root = ElementTree.fromstring(response_text)

            # Check for API errors
            status = root.get("status")
            if status != "success":
                error_msg = "Unknown error"
                error_element = root.find(".//msg")
                if error_element is not None and error_element.text is not None:
                    error_msg = error_element.text
                raise ValueError(f"API error: {error_msg}") from None

            return root
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            raise httpx.HTTPError(f"HTTP error: {str(e)}") from e
        except ElementTree.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            raise ValueError(f"Failed to parse XML response: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}") from e

    async def get_system_info(self) -> SystemInfo:
        """Get system information from the firewall.

        Returns:
            SystemInfo object containing system information.

        """
        # Use the correct XML command format that works with this firewall
        params = {"type": "op", "cmd": "<show><system><info></info></system></show>"}

        root = await self._make_request(params)
        result = root.find(".//result")

        if result is None:
            raise ValueError("No system information found in response")

        # Extract system information
        system_info_dict: dict[str, Any] = {
            "hostname": "",
            "ip_address": "",
            "netmask": "",
            "default_gateway": "",
            "mac_address": "",
            "time": "",
            "uptime": "",
            "version": "",
            "gp_version": None,
        }

        # Handle the case where result has a 'system' child element
        system_elem = result.find("system")
        if system_elem is not None:
            for child in system_elem:
                if child.text is not None and child.tag in system_info_dict:
                    system_info_dict[child.tag] = child.text
        else:
            # Handle the case where result contains the system info directly
            for child in result:
                if child.text is not None and child.tag in system_info_dict:
                    system_info_dict[child.tag] = child.text

        # Create and return the SystemInfo object
        return SystemInfo(**system_info_dict)

    async def get_address_objects(self) -> list[AddressObject]:
        """Get address objects configured on the firewall.

        Returns:
            List of AddressObject objects containing address object information.
            Each object contains name, type, value, and optionally description and location.

        """
        address_objects = []
        logger.info("Retrieving address objects from Panorama")

        # 1. Get shared address objects
        shared_params = {
            "type": "config",
            "action": "get",
            "xpath": "/config/shared/address",
        }
        try:
            logger.info("Retrieving shared address objects")
            root = await self._make_request(shared_params)

            # Log the structure of the response for debugging
            logger.debug(f"Shared address response structure: {ElementTree.tostring(root, encoding='unicode')[:200]}...")

            shared_entries = root.findall(".//entry")
            logger.info(f"Found {len(shared_entries)} shared address objects")

            for entry in shared_entries:
                address_obj = AddressObject(
                    name=entry.get("name") or "",
                    location="shared",
                    type="ip-netmask",  # default type
                    value="",  # will be updated in _process_address_entry
                    description=None,
                )

                # Process the address object
                address_objects.append(self._process_address_entry(entry, address_obj))

        except Exception as e:
            logger.error(f"Error retrieving shared address objects: {str(e)}")

        # 2. Get device group address objects
        try:
            # First, get the list of device groups
            logger.info("Retrieving device groups")
            dg_list_params = {
                "type": "config",
                "action": "get",
                "xpath": "/config/devices/entry/device-group",
            }
            dg_root = await self._make_request(dg_list_params)

            # Log the structure of the response for debugging
            logger.debug(f"Device group response structure: {ElementTree.tostring(dg_root, encoding='unicode')[:200]}...")

            device_groups = dg_root.findall(".//entry")
            logger.info(f"Found {len(device_groups)} device groups")

            for dg in device_groups:
                dg_name = dg.get("name")
                if not dg_name:
                    continue

                logger.info(f"Retrieving address objects for device group '{dg_name}'")
                # Get addresses for this device group
                dg_addr_params = {
                    "type": "config",
                    "action": "get",
                    "xpath": f"/config/devices/entry/device-group/entry[@name='{dg_name}']/address",
                }

                try:
                    dg_addr_root = await self._make_request(dg_addr_params)

                    # Log the structure of the response for debugging
                    logger.debug(
                        f"Device group '{dg_name}' address response: "
                        f"{ElementTree.tostring(dg_addr_root, encoding='unicode')[:200]}..."
                    )

                    dg_entries = dg_addr_root.findall(".//entry")
                    logger.info(f"Found {len(dg_entries)} address objects in device group '{dg_name}'")

                    for entry in dg_entries:
                        address_obj = AddressObject(
                            name=entry.get("name") or "",
                            location=f"device-group:{dg_name}",
                            type="ip-netmask",  # default type
                            value="",  # will be updated in _process_address_entry
                            description=None,
                        )

                        # Process the address object
                        address_objects.append(self._process_address_entry(entry, address_obj))

                except Exception as e:
                    logger.error(f"Error retrieving address objects for device group '{dg_name}': {str(e)}")

        except Exception as e:
            logger.error(f"Error retrieving device groups: {str(e)}")

        # 3. Get vsys address objects (for backward compatibility with firewalls)
        logger.info("Retrieving vsys address objects (for backward compatibility)")
        vsys_params = {
            "type": "config",
            "action": "get",
            "xpath": "/config/devices/entry/vsys/entry/address",
        }
        try:
            root = await self._make_request(vsys_params)
            vsys_entries = root.findall(".//entry")
            logger.info(f"Found {len(vsys_entries)} vsys address objects")

            # Find vsys name from the xpath rather than parent reference
            # since standard ElementTree doesn't have getparent()
            for entry in vsys_entries:
                # Default to "unknown" if we can't determine the vsys name
                vsys_name = "unknown"
                address_obj = AddressObject(
                    name=entry.get("name") or "",
                    location=f"vsys:{vsys_name}",
                    type="ip-netmask",  # default type
                    value="",  # will be updated in _process_address_entry
                    description=None,
                )

                # Process the address object
                address_objects.append(self._process_address_entry(entry, address_obj))

        except Exception as e:
            # This might fail on Panorama, which is expected
            logger.debug(f"Note: vsys address objects retrieval: {str(e)}")

        logger.info(f"Total address objects found: {len(address_objects)}")
        return address_objects

    def _process_address_entry(self, entry: ElementTree.Element, address_obj: AddressObject) -> AddressObject:
        """Process an address object entry from the XML response.

        Args:
            entry: XML element containing address object information
            address_obj: Existing AddressObject to update

        Returns:
            Updated AddressObject

        """
        # Create a dictionary to store the updates
        updates: dict[str, Any] = {
            "name": address_obj.name,
            "location": address_obj.location,
            "type": address_obj.type,
            "value": "",  # will be updated below
            "description": None,
            "tags": [],
        }

        # Process type and value
        if entry.find("ip-netmask") is not None:
            updates["type"] = "ip-netmask"
            value_elem = entry.find("ip-netmask")
        elif entry.find("ip-range") is not None:
            updates["type"] = "ip-range"
            value_elem = entry.find("ip-range")
        elif entry.find("fqdn") is not None:
            updates["type"] = "fqdn"
            value_elem = entry.find("fqdn")
        else:
            logger.warning(f"Unknown address type for entry: {entry.get('name')}")
            return address_obj

        # Get the value
        if value_elem is not None and value_elem.text:
            updates["value"] = value_elem.text

        # Get description if present
        description = entry.find("description")
        if description is not None and description.text:
            updates["description"] = description.text

        # Process tags
        tag_elems = entry.findall(".//member")
        if tag_elems:
            updates["tags"] = [tag.text for tag in tag_elems if tag.text is not None]

        # Create a new AddressObject with the updates
        return AddressObject(**updates)

    async def get_security_zones(self) -> list[dict[str, Any]]:
        """Get security zones from the firewall.

        Returns:
            List of security zone dictionaries.

        Raises:
            PanosConnectionError: If connection to the firewall fails
            PanosAuthenticationError: If authentication fails
            PanosOperationError: If the operation fails
        """
        try:
            response = await self._make_request(
                {
                    "type": "config",
                    "action": "get",
                    "xpath": "/config/devices/entry/vsys/entry/zone",
                }
            )

            # Extract zones from the response
            zones = response.findall(".//entry")
            if not zones:
                return []

            # Ensure we have a list of zones
            if not isinstance(zones, list):
                zones = [zones]

            # Process each zone
            processed_zones = []
            for zone in zones:
                if not isinstance(zone, dict):
                    continue

                zone_dict = {
                    "name": zone.get("@name", ""),
                    "type": "layer3",  # Default to layer3
                    "location": "vsys1",
                    "interfaces": [],
                    "user_identification": False,
                    "device_identification": False,
                    "packet_buffer_protection": False,
                }

                # Extract zone type
                for zone_type in ["layer3", "layer2", "virtual-wire", "tap"]:
                    if zone.get(zone_type) is not None:
                        zone_dict["type"] = zone_type
                        break

                # Extract interfaces
                zone_type = zone_dict["type"]
                interface_section = zone.get(zone_type, {})
                if isinstance(interface_section, dict):
                    member_list = interface_section.get("member", [])
                    if member_list:
                        if isinstance(member_list, list):
                            zone_dict["interfaces"] = member_list
                        else:
                            zone_dict["interfaces"] = [member_list]

                # Extract advanced options
                network = zone.get("network", {})
                if isinstance(network, dict):
                    zone_dict["user_identification"] = network.get("user-acl") is not None
                    zone_dict["device_identification"] = network.get("device-acl") is not None
                    zone_dict["packet_buffer_protection"] = network.get("pbf") is not None

                processed_zones.append(zone_dict)

            return processed_zones

        except PanosError:
            raise
        except Exception as e:
            raise PanosOperationError(f"Failed to retrieve security zones: {str(e)}") from e


class PANOSClient:
    """Client for interacting with PAN-OS XML API."""

    def __init__(self, hostname: str, api_key: str) -> None:
        """Initialize the client.

        Args:
            hostname: The hostname or IP address of the PAN-OS device
            api_key: The API key for authentication
        """
        self.hostname = hostname
        self.api_key = api_key
        self.base_url = f"https://{hostname}/api"
        self.client = httpx.AsyncClient(verify=False)

    async def get_system_info(self) -> SystemInfo:
        """Get system information from the firewall."""
        raise NotImplementedError("Method not implemented")

    async def get_address_objects(self) -> list[AddressObject]:
        """Get address objects from the firewall."""
        raise NotImplementedError("Method not implemented")

    async def get_security_zones(self) -> list[dict[str, Any]]:
        """Get security zones from the firewall."""
        raise NotImplementedError("Method not implemented")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
