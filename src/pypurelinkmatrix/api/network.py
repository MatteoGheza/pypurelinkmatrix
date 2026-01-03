"""Network configuration API."""

import logging
import re

from ..exceptions import DeviceError
from ..http_client import post_request

logger = logging.getLogger(__name__)


class NetworkAPI:
    """API for network configuration operations."""

    def __init__(self, session, base_url: str):
        """Initialize network API.

        Args:
            session: Requests session for HTTP communication
            base_url: Base URL of the device
        """
        self.session = session
        self.base_url = base_url
        self.endpoint = "ip.set"

    def configure_static_ip(
        self,
        ip_address: str,
        subnet_mask: str,
        gateway: str,
        timeout: int = 30,
    ) -> bool:
        """Configure static IP address and network settings.

        Args:
            ip_address: IP address (e.g., '192.168.1.100')
            subnet_mask: Subnet mask (e.g., '255.255.255.0')
            gateway: Default gateway (e.g., '192.168.1.1')
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If any parameter format is invalid
            DeviceError: If configuration fails

        Example:
            >>> api.configure_static_ip(
            ...     '192.168.1.100',
            ...     '255.255.255.0',
            ...     '192.168.1.1'
            ... )
        """
        # Validate all parameters
        self._validate_ip(ip_address, "IP address")
        self._validate_ip(subnet_mask, "Subnet mask")
        self._validate_ip(gateway, "Gateway")

        # Check that IP and gateway are on the same network
        if not self._ip_in_subnet(ip_address, subnet_mask, gateway):
            raise ValueError("Gateway address must be on the same network as IP address")

        try:
            cmd = f"#ip ip={ip_address} mask={subnet_mask} " f"gw={gateway}"
            logger.debug(f"Configuring static IP: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info(
                f"Configured static IP: {ip_address}, " f"Mask: {subnet_mask}, Gateway: {gateway}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to configure static IP: {e}")
            raise DeviceError(f"Static IP configuration failed: {e}") from e

    def enable_dhcp(self, timeout: int = 30) -> bool:
        """Enable DHCP for automatic IP configuration.

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            DeviceError: If operation fails

        Example:
            >>> api.enable_dhcp()
        """
        return self._set_dhcp(True, timeout)

    def disable_dhcp(self, timeout: int = 30) -> bool:
        """Disable DHCP for static IP configuration.

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            DeviceError: If operation fails

        Example:
            >>> api.disable_dhcp()
        """
        return self._set_dhcp(False, timeout)

    def _set_dhcp(self, enabled: bool, timeout: int) -> bool:
        """Set DHCP enabled/disabled state.

        Args:
            enabled: True to enable DHCP, False to disable
            timeout: Request timeout in seconds

        Returns:
            True if successful

        Raises:
            DeviceError: If operation fails
        """
        try:
            # Device uses 0 for DHCP on, 1 for DHCP off
            dhcp_value = 0 if enabled else 1

            cmd = f"#ip dhcp={dhcp_value}"
            logger.debug(f"Setting DHCP: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()

            status = "enabled" if enabled else "disabled"
            logger.info(f"DHCP {status}")

            return True

        except Exception as e:
            logger.error(f"Failed to set DHCP: {e}")
            raise DeviceError(f"DHCP configuration failed: {e}") from e

    @staticmethod
    def _validate_ip(ip: str, label: str = "IP address") -> None:
        """Validate IP address format.

        Args:
            ip: IP address to validate
            label: Label for error messages

        Raises:
            ValueError: If IP format is invalid
        """
        if not ip or not isinstance(ip, str):
            raise ValueError(f"{label} must be a non-empty string")

        pattern = re.compile(
            r"^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\."
            r"(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\."
            r"(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\."
            r"(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$"
        )

        if not pattern.match(ip):
            raise ValueError(
                f"{label} format is invalid. Must be in format " "xxx.xxx.xxx.xxx (0-255 per octet)"
            )

    @staticmethod
    def _ip_in_subnet(ip: str, subnet_mask: str, gateway: str) -> bool:
        """Check if gateway is on the same subnet as IP.

        Args:
            ip: IP address
            subnet_mask: Subnet mask
            gateway: Gateway address

        Returns:
            True if gateway is on the same subnet
        """

        def ip_to_int(ip_str: str) -> int:
            parts = [int(x) for x in ip_str.split(".")]
            return (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]

        ip_int = ip_to_int(ip)
        mask_int = ip_to_int(subnet_mask)
        gateway_int = ip_to_int(gateway)

        # Check if they're on the same subnet
        return (ip_int & mask_int) == (gateway_int & mask_int)
