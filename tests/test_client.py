"""Tests for PureLink client."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from pypurelinkmatrix import PureLinkClient
from pypurelinkmatrix.exceptions import (
    AuthenticationError,
    PureLinkConnectionError,
    ValidationError,
)


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    session = MagicMock(spec=aiohttp.ClientSession)
    return session


class TestPureLinkClientInitialization:
    """Test client initialization."""

    def test_init_with_all_params(self, mock_session):
        """Test initialization with all parameters."""
        client = PureLinkClient(
            websession=mock_session,
            host="127.0.0.1",
            username="admin",
            password="password",
            use_https=True,
            verify_ssl=False,
        )
        assert client.host == "127.0.0.1"
        assert client.auth.username == "admin"
        assert client.auth.password == "password"
        assert client.auth.use_https is True
        assert client.auth.verify_ssl is False
        assert client.auth.is_authenticated is False

    def test_init_with_minimal_params(self, mock_session):
        """Test initialization with minimal parameters."""
        client = PureLinkClient(websession=mock_session, host="device.local")
        assert client.host == "device.local"
        assert client.auth.username == ""
        assert client.auth.password == ""
        assert client.auth.use_https is False
        assert client.auth.verify_ssl is True

    def test_init_host_whitespace_trimmed(self, mock_session):
        """Test that host whitespace is trimmed."""
        client = PureLinkClient(websession=mock_session, host="  127.0.0.1  ")
        assert client.host == "127.0.0.1"

    def test_init_invalid_host_empty(self, mock_session):
        """Test initialization with empty host."""
        with pytest.raises(ValidationError):
            PureLinkClient(websession=mock_session, host="")


class TestCredentialValidation:
    """Test credential validation."""

    def test_valid_credentials(self):
        """Test validation of valid credentials."""
        # Should not raise
        PureLinkClient._validate_credentials("admin", "password123")
        PureLinkClient._validate_credentials("user_01", "pass_99")
        PureLinkClient._validate_credentials("a", "b")

    def test_empty_username(self):
        """Test validation with empty username."""
        with pytest.raises(ValidationError, match="Username cannot be empty"):
            PureLinkClient._validate_credentials("", "password")

    def test_empty_password(self):
        """Test validation with empty password."""
        with pytest.raises(ValidationError, match="Password cannot be empty"):
            PureLinkClient._validate_credentials("admin", "")

    def test_username_too_long(self):
        """Test validation with username exceeding 15 characters."""
        with pytest.raises(ValidationError, match="Username length must be 1-15"):
            PureLinkClient._validate_credentials("username_toolong", "password")

    def test_password_too_long(self):
        """Test validation with password exceeding 15 characters."""
        with pytest.raises(ValidationError, match="Password length must be 1-15"):
            PureLinkClient._validate_credentials("admin", "password_toolong")

    def test_username_invalid_chars(self):
        """Test validation with invalid characters in username."""
        invalid_usernames = [
            "admin@",
            "user-name",
            "user.name",
            "user name",
            "user!",
        ]
        for username in invalid_usernames:
            with pytest.raises(ValidationError, match="only letters, numbers, and underscores"):
                PureLinkClient._validate_credentials(username, "password")

    def test_password_invalid_chars(self):
        """Test validation with invalid characters in password."""
        invalid_passwords = [
            "pass@word",
            "pass-word",
            "pass.word",
            "pass word",
            "pass!",
        ]
        for password in invalid_passwords:
            with pytest.raises(ValidationError, match="only letters, numbers, and underscores"):
                PureLinkClient._validate_credentials("admin", password)


@pytest.mark.asyncio
class TestLogin:
    """Test login functionality."""

    async def test_login_success(self, mock_session):
        """Test successful login."""
        mock_response = AsyncMock()
        mock_response.text.return_value = 'settingsLoginCallback({"status":"1","str":""});'
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__.return_value = mock_response

        mock_session.post.return_value = mock_response

        client = PureLinkClient(
            mock_session, host="127.0.0.1", username="admin", password="password"
        )
        result = await client.async_login()

        assert result is True
        assert client.auth.is_authenticated is True
        mock_session.post.assert_called_once()

    async def test_login_failure(self, mock_session):
        """Test failed login."""
        mock_response = AsyncMock()
        mock_response.text.return_value = 'settingsLoginCallback({"status":"0","str":""});'
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__.return_value = mock_response

        mock_session.post.return_value = mock_response

        client = PureLinkClient(
            mock_session, host="127.0.0.1", username="admin", password="password"
        )

        with pytest.raises(AuthenticationError):
            await client.async_login()

        assert client.auth.is_authenticated is False

    async def test_login_connection_error(self, mock_session):
        """Test login with connection error."""
        mock_session.post.side_effect = aiohttp.ClientError("Connection failed")

        client = PureLinkClient(
            mock_session, host="127.0.0.1", username="admin", password="password"
        )

        with pytest.raises(PureLinkConnectionError):
            await client.async_login()


class TestLogout:
    """Test logout functionality."""

    def test_logout(self, mock_session):
        """Test logout."""
        client = PureLinkClient(mock_session, host="127.0.0.1")
        client.auth.is_authenticated = True

        result = client.logout()

        assert result is True
        assert client.auth.is_authenticated is False


class TestRepresentation:
    """Test string representation."""

    def test_repr_not_authenticated(self, mock_session):
        """Test repr when not authenticated."""
        client = PureLinkClient(
            mock_session, host="127.0.0.1", username="admin", password="password"
        )
        repr_str = repr(client)

        assert "127.0.0.1" in repr_str
        assert "admin" in repr_str
        assert "not authenticated" in repr_str

    def test_repr_authenticated(self, mock_session):
        """Test repr when authenticated."""
        client = PureLinkClient(
            mock_session, host="127.0.0.1", username="admin", password="password"
        )
        client.auth.is_authenticated = True
        repr_str = repr(client)

        assert "127.0.0.1" in repr_str
        assert "admin" in repr_str
        assert "authenticated" in repr_str
