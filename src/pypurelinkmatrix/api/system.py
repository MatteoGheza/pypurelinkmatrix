"""System configuration and management API."""

import logging
import re

from ..exceptions import DeviceError
from ..http_client import post_request

logger = logging.getLogger(__name__)


class SystemAPI:
    """API for system configuration and management operations."""

    def __init__(self, session, base_url: str):
        """Initialize system API.

        Args:
            session: Requests session for HTTP communication
            base_url: Base URL of the device
        """
        self.session = session
        self.base_url = base_url
        self.endpoint = "system_set"

    def reboot(self, timeout: int = 30) -> bool:
        """Reboot the device.

        Initiates a system reboot. The device will disconnect during the
        reboot process.

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if reboot command was sent successfully

        Raises:
            DeviceError: If operation fails

        Example:
            >>> api.reboot()
        """
        try:
            cmd = "#power start=1"
            logger.debug(f"Sending reboot command: {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.warning("Device reboot initiated")

            return True

        except Exception as e:
            logger.error(f"Failed to reboot device: {e}")
            raise DeviceError(f"Reboot command failed: {e}") from e

    def factory_reset_common(self, timeout: int = 30) -> bool:
        """Perform factory reset of common settings.

        Resets the following to factory defaults:
        - Video matrix settings
        - Audio settings
        - EDID configuration
        - Network settings

        Preserves:
        - Presets and custom names
        - User EDID profiles

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if reset command was sent successfully

        Raises:
            DeviceError: If operation fails

        Example:
            >>> api.factory_reset_common()
        """
        try:
            cmd = "#factory0"
            logger.debug(f"Sending factory reset (common): {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.warning("Factory reset (common settings) initiated")

            return True

        except Exception as e:
            logger.error(f"Failed to perform factory reset: {e}")
            raise DeviceError(f"Factory reset failed: {e}") from e

    def factory_reset_all(self, timeout: int = 30) -> bool:
        """Perform complete factory reset.

        Resets all settings to factory defaults, including:
        - Video matrix settings
        - Audio settings
        - EDID configuration
        - Network settings
        - Presets and custom names
        - User EDID profiles
        - All user data

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if reset command was sent successfully

        Raises:
            DeviceError: If operation fails

        Example:
            >>> api.factory_reset_all()
        """
        try:
            cmd = "#factory1"
            logger.debug(f"Sending factory reset (all): {cmd}")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.warning("Factory reset (all settings) initiated")

            return True

        except Exception as e:
            logger.error(f"Failed to perform complete factory reset: {e}")
            raise DeviceError(f"Complete factory reset failed: {e}") from e

    def change_password(self, username: str, password: str, timeout: int = 30) -> bool:
        """Change or create user password.

        Updates the password for a user. If the user doesn't exist, creates it.

        Args:
            username: Username (1-15 alphanumeric/underscore chars)
            password: New password (1-15 alphanumeric/underscore chars)
            timeout: Request timeout in seconds

        Returns:
            True if password change was successful

        Raises:
            ValueError: If username or password format is invalid
            DeviceError: If operation fails

        Example:
            >>> api.change_password('admin', 'newpass123')
        """
        # Validate credentials
        self._validate_credentials(username, password)

        try:
            # Note: Using base64 encoding as per device requirement
            cmd = f"#register255 id={username} psd={password}"
            logger.debug("Sending password change command")

            response = post_request(
                self.session,
                self.base_url,
                self.endpoint,
                cmd,
                timeout=timeout,
            )
            response.raise_for_status()
            logger.info(f"Password changed for user '{username}'")

            return True

        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            raise DeviceError(f"Password change failed: {e}") from e

    @staticmethod
    def _validate_credentials(username: str, password: str) -> None:
        """Validate username and password format.

        Args:
            username: Username to validate
            password: Password to validate

        Raises:
            ValueError: If format is invalid
        """
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")

        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")

        if len(username) > 15:
            raise ValueError("Username must be 15 characters or less")

        if len(password) > 15:
            raise ValueError("Password must be 15 characters or less")

        pattern = re.compile(r"^[a-zA-Z0-9_]{1,15}$")

        if not pattern.match(username):
            raise ValueError("Username must contain only letters, numbers, and underscores")

        if not pattern.match(password):
            raise ValueError("Password must contain only letters, numbers, and underscores")
