"""PureLink Matrix device connection client."""

import base64
import logging
import re
from typing import Optional
from urllib.parse import urljoin

import requests

from .api.audio import AudioAPI
from .api.edid import EDIDAPI
from .api.network import NetworkAPI
from .api.system import SystemAPI
from .api.video import VideoAPI
from .exceptions import AuthenticationError, PureLinkConnectionError, ValidationError
from .models import DeviceState

logger = logging.getLogger(__name__)

# Validation patterns based on JS example
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{1,15}$")
PASSWORD_PATTERN = re.compile(r"^[a-zA-Z0-9_]{1,15}$")


class PureLinkClient:
    """Client for connecting to and managing PureLink matrix devices.

    This class handles authentication and communication with PureLink
    matrix switching devices.

    Attributes:
        host: The device host address or IP
        username: Username for authentication
        session: Requests session for HTTP communication
    """

    def __init__(
        self,
        host: str,
        username: str = "",
        password: str = "",
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """Initialize the PureLink client.

        Args:
            host: Device host address or IP (e.g., '192.168.1.100' or 'matrix.local')
            username: Username for authentication (1-15 alphanumeric/underscore chars)
            password: Password for authentication (1-15 alphanumeric/underscore chars)
            timeout: Request timeout in seconds. Defaults to 30.
            verify_ssl: Whether to verify SSL certificates. Defaults to True.

        Raises:
            ValidationError: If host, username, or password format is invalid.
        """
        self.host = self._validate_host(host)
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.is_authenticated = False
        self._base_url = self._build_base_url()

        # Initialize API modules
        self.video = VideoAPI(self.session, self._base_url)
        self.audio = AudioAPI(self.session, self._base_url)
        self.edid = EDIDAPI(self.session, self._base_url)
        self.network = NetworkAPI(self.session, self._base_url)
        self.system = SystemAPI(self.session, self._base_url)

        # Device state
        self.state = DeviceState()

        logger.debug(f"PureLinkClient initialized for host: {self.host}")

    def _validate_host(self, host: str) -> str:
        """Validate and normalize the host address.

        Args:
            host: The host address to validate

        Returns:
            The normalized host address

        Raises:
            ValidationError: If host is empty
        """
        if not host or not isinstance(host, str):
            raise ValidationError("Host must be a non-empty string")
        return host.strip()

    @staticmethod
    def _validate_credentials(username: str, password: str) -> None:
        """Validate username and password format.

        Based on PureLink device requirements:
        - Length: 1-15 characters
        - Allowed characters: letters (a-z, A-Z), numbers (0-9), underscore (_)

        Args:
            username: Username to validate
            password: Password to validate

        Raises:
            ValidationError: If credentials don't match the required pattern
        """
        if not username:
            raise ValidationError("Username cannot be empty")
        if not password:
            raise ValidationError("Password cannot be empty")

        if len(username) < 1 or len(username) > 15:
            raise ValidationError(f"Username length must be 1-15 characters (got {len(username)})")

        if not USERNAME_PATTERN.match(username):
            raise ValidationError("Username must contain only letters, numbers, and underscores")

        if len(password) < 1 or len(password) > 15:
            raise ValidationError(f"Password length must be 1-15 characters (got {len(password)})")

        if not PASSWORD_PATTERN.match(password):
            raise ValidationError("Password must contain only letters, numbers, and underscores")

    def _build_base_url(self) -> str:
        """Build the base URL for API requests.

        Returns:
            The base URL for the device
        """
        protocol = "https" if self.verify_ssl else "http"
        return f"{protocol}://{self.host}"

    @staticmethod
    def _encode_credentials(username: str, password: str) -> tuple[str, str]:
        """Encode credentials using base64.

        Follows the same encoding method as the JS example.

        Args:
            username: Username to encode
            password: Password to encode

        Returns:
            Tuple of (encoded_username, encoded_password)
        """
        encoded_username = base64.b64encode(username.encode("utf-8")).decode("utf-8")
        encoded_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")
        return encoded_username, encoded_password

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Authenticate with the PureLink device.

        Validates credentials and sends login request to device.
        Credentials can be provided at initialization or at login time.

        Args:
            username: Username for login. If not provided, uses instance username.
            password: Password for login. If not provided, uses instance password.

        Returns:
            True if authentication was successful

        Raises:
            ValidationError: If credentials format is invalid
            AuthenticationError: If authentication fails
            PureLinkConnectionError: If device connection fails

        Example:
            >>> client = PureLinkClient(host="192.168.1.100")
            >>> client.login("admin", "password")
            True
        """
        # Use provided credentials or fall back to instance credentials
        username = username or self.username
        password = password or self.password

        # Validate credentials
        try:
            self._validate_credentials(username, password)
        except ValidationError as e:
            logger.error(f"Credential validation failed: {e}")
            raise

        # Update instance credentials if provided at login time
        if username != self.username:
            self.username = username
        if password != self.password:
            self.password = password

        # Encode credentials
        encoded_username, encoded_password = self._encode_credentials(username, password)

        logger.debug(f"Attempting login for user: {username}")

        try:
            # Prepare login request following the device API format
            # Based on JS: login.doPost('#login id='+user_name+' psd='+password);
            url = urljoin(self._base_url, "login.set")
            body = f"#login id={encoded_username} psd={encoded_password}"

            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ISAJAX": "yes",
            }

            response = self.session.post(
                url,
                data=body,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            response.raise_for_status()

            # Parse response (device returns status: 0 for fail, 1 for success)
            response_text = response.text.strip()
            logger.debug(f"Login response: {response_text}")

            # Try to parse response as JavaScript object notation
            # Looking for status field in response
            if "status" in response_text:
                # Simple check for success status
                if "status" in response_text and "0" not in response_text.split("status")[1][:5]:
                    self.is_authenticated = True
                    logger.info(f"Successfully authenticated as {username}")
                    return True
                else:
                    raise AuthenticationError("Invalid username or password")
            else:
                # If no status field, treat non-empty response as success
                if response_text:
                    self.is_authenticated = True
                    logger.info(f"Successfully authenticated as {username}")
                    return True
                else:
                    raise AuthenticationError("Empty response from device")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise PureLinkConnectionError(f"Failed to connect to device at {self.host}: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise PureLinkConnectionError(f"Connection to {self.host} timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise PureLinkConnectionError(f"Request failed: {e}") from e

    def logout(self) -> bool:
        """Logout from the device.

        Returns:
            True if logout was successful
        """
        self.is_authenticated = False
        logger.info("Logged out from device")
        return True

    def close(self) -> None:
        """Close the client session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.debug("Client session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        auth_status = "authenticated" if self.is_authenticated else "not authenticated"
        return f"PureLinkClient(host={self.host}, user={self.username}, {auth_status})"
