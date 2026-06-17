"""PureLink Matrix device connection client."""

import logging
import re

from aiohttp import ClientSession

from .api.audio import AudioAPI
from .api.edid import EDIDAPI
from .api.network import NetworkAPI
from .api.status import StatusAPI
from .api.system import SystemAPI
from .api.video import VideoAPI
from .auth import PureLinkAuth
from .exceptions import ValidationError
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
        auth: PureLinkAuth instance for authenticated requests
        state: Local device state representation
    """

    def __init__(
        self,
        websession: ClientSession,
        host: str,
        username: str = "",
        password: str = "",
        use_https: bool = False,
        verify_ssl: bool = True,
    ):
        """Initialize the PureLink client.

        Args:
            websession: aiohttp ClientSession to use
            host: Device host address or IP (e.g., '192.168.1.100' or 'matrix.local')
            username: Username for authentication (1-15 alphanumeric/underscore chars)
            password: Password for authentication (1-15 alphanumeric/underscore chars)
            use_https: Whether to use HTTPS for connections. Defaults to False.
            verify_ssl: Whether to verify SSL certificates. Defaults to True.

        Raises:
            ValidationError: If host, username, or password format is invalid.
        """
        self.host = self._validate_host(host)

        # Validate credentials if provided
        if username or password:
            self._validate_credentials(username, password)

        self.auth = PureLinkAuth(
            websession,
            host=self.host,
            username=username,
            password=password,
            use_https=use_https,
            verify_ssl=verify_ssl,
        )

        # Device state (initialize first so APIs can reference it)
        self.state = DeviceState()

        # Initialize API modules
        self.video = VideoAPI(self.auth, self.state)
        self.audio = AudioAPI(self.auth, self.state)
        self.edid = EDIDAPI(self.auth, self.state)
        self.network = NetworkAPI(self.auth)
        self.system = SystemAPI(self.auth)
        self.status = StatusAPI(self.auth)

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

    async def async_login(self) -> bool:
        """Authenticate with the PureLink device.

        Returns:
            True if authentication was successful
        """
        return await self.auth.login()

    def logout(self) -> bool:
        """Logout from the device.

        Returns:
            True if logout was successful
        """
        self.auth.is_authenticated = False
        logger.info("Logged out from device")
        return True

    def __repr__(self) -> str:
        """String representation of the client."""
        auth_status = "authenticated" if self.auth.is_authenticated else "not authenticated"
        return f"PureLinkClient(host={self.host}, user={self.auth.username}, {auth_status})"
