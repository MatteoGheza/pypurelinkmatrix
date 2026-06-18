"""Authentication and request handling for PureLink matrix devices."""

import base64
import logging
import time
from typing import Any

import aiohttp
from aiohttp import ClientResponse, ClientSession

from .exceptions import AuthenticationError, PureLinkConnectionError

logger = logging.getLogger(__name__)


class PureLinkAuth:
    """Class to make authenticated requests to PureLink devices."""

    def __init__(
        self,
        websession: ClientSession,
        host: str,
        username: str = "",
        password: str = "",
        use_https: bool = False,
        verify_ssl: bool = True,
    ):
        """Initialize the auth.

        Args:
            websession: aiohttp ClientSession to use
            host: Device host address or IP
            username: Username for authentication
            password: Password for authentication
            use_https: Whether to use HTTPS
            verify_ssl: Whether to verify SSL certificates
        """
        self.websession = websession
        self.host = host
        self.username = username
        self.password = password
        self.use_https = use_https
        self.verify_ssl = verify_ssl
        self.is_authenticated = False

        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}"

    def get_timestamped_endpoint(self, endpoint: str) -> str:
        """Get endpoint with appended Unix timestamp in milliseconds."""
        timestamp = int(time.time() * 1000)
        return f"{endpoint}{timestamp}"

    async def login(self) -> bool:
        """Authenticate with the device."""
        if not self.username or not self.password:
            raise AuthenticationError("Username and password are required for login")

        encoded_user = base64.b64encode(self.username.encode("utf-8")).decode("utf-8")
        encoded_pass = base64.b64encode(self.password.encode("utf-8")).decode("utf-8")

        endpoint = self.get_timestamped_endpoint("login.set")
        url = f"{self.base_url}/{endpoint}"
        body = f"#login id={encoded_user} psd={encoded_pass}"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "ISAJAX": "yes",
        }

        try:
            async with self.websession.post(
                url,
                data=body,
                headers=headers,
                ssl=self.verify_ssl if self.use_https else None,
            ) as response:
                response.raise_for_status()
                text = await response.text()
                logger.debug(f"Login response: {text}")

                # Parse response: settingsLoginCallback({"status":"1","str":""});
                if '"status":"1"' in text:
                    self.is_authenticated = True
                    logger.info(f"Successfully authenticated as {self.username}")
                    return True
                else:
                    raise AuthenticationError("Invalid username or password")

        except aiohttp.ClientError as e:
            logger.error(f"Connection error during login: {e}")
            raise PureLinkConnectionError(f"Failed to connect to device at {self.host}: {e}") from e

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> ClientResponse:
        """Make a request to the device, logging in if necessary."""
        if not self.is_authenticated and endpoint != "login.set":
            await self.login()

        timestamped_endpoint = self.get_timestamped_endpoint(endpoint)
        url = f"{self.base_url}/{timestamped_endpoint}"

        if "ssl" not in kwargs and self.use_https:  # pragma: no cover
            kwargs["ssl"] = self.verify_ssl

        logger.debug(f"Making {method.upper()} request to {url}")

        try:
            return await self.websession.request(method, url, **kwargs)
        except aiohttp.ClientError as e:
            logger.error(f"Request error: {e}")
            raise PureLinkConnectionError(f"Request to {url} failed: {e}") from e
