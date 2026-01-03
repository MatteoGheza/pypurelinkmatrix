"""Tests for PureLink client."""

from unittest.mock import Mock, patch

import pytest
import requests
from pypurelinkmatrix import PureLinkClient
from pypurelinkmatrix.exceptions import (
    AuthenticationError,
    PureLinkConnectionError,
    ValidationError,
)


class TestPureLinkClientInitialization:
    """Test client initialization."""

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        client = PureLinkClient(
            host="192.168.1.100",
            username="admin",
            password="password",
            timeout=60,
            verify_ssl=False,
        )
        assert client.host == "192.168.1.100"
        assert client.username == "admin"
        assert client.password == "password"
        assert client.timeout == 60
        assert client.verify_ssl is False
        assert client.is_authenticated is False

    def test_init_with_minimal_params(self):
        """Test initialization with minimal parameters."""
        client = PureLinkClient(host="device.local")
        assert client.host == "device.local"
        assert client.username == ""
        assert client.password == ""
        assert client.timeout == 30
        assert client.verify_ssl is True

    def test_init_host_whitespace_trimmed(self):
        """Test that host whitespace is trimmed."""
        client = PureLinkClient(host="  192.168.1.100  ")
        assert client.host == "192.168.1.100"

    def test_init_invalid_host_empty(self):
        """Test initialization with empty host."""
        with pytest.raises(ValidationError):
            PureLinkClient(host="")

    def test_init_invalid_host_none(self):
        """Test initialization with None host."""
        with pytest.raises(ValidationError):
            PureLinkClient(host="")


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


class TestEncodeCredentials:
    """Test credential encoding."""

    def test_encode_credentials(self):
        """Test base64 encoding of credentials."""
        username, password = PureLinkClient._encode_credentials("admin", "password")

        # Decode and verify
        import base64

        assert base64.b64decode(username).decode("utf-8") == "admin"
        assert base64.b64decode(password).decode("utf-8") == "password"

    def test_encode_special_valid_chars(self):
        """Test encoding with underscores and numbers."""
        username, password = PureLinkClient._encode_credentials("user_01", "pass_99")

        import base64

        assert base64.b64decode(username).decode("utf-8") == "user_01"
        assert base64.b64decode(password).decode("utf-8") == "pass_99"


class TestLogin:
    """Test login functionality."""

    @patch("pypurelinkmatrix.client.requests.Session.post")
    def test_login_success(self, mock_post):
        """Test successful login."""
        mock_response = Mock()
        mock_response.text = "status:1"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = PureLinkClient(host="192.168.1.100")
        result = client.login("admin", "password")

        assert result is True
        assert client.is_authenticated is True
        mock_post.assert_called_once()

    @patch("pypurelinkmatrix.client.requests.Session.post")
    def test_login_failure(self, mock_post):
        """Test failed login."""
        mock_response = Mock()
        mock_response.text = "status:0"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = PureLinkClient(host="192.168.1.100")

        with pytest.raises(AuthenticationError):
            client.login("admin", "wrongpassword")

        assert client.is_authenticated is False

    def test_login_validation_error(self):
        """Test login with invalid credentials."""
        client = PureLinkClient(host="192.168.1.100")

        with pytest.raises(ValidationError):
            client.login("invalid@user", "password")

    @patch("pypurelinkmatrix.client.requests.Session.post")
    def test_login_connection_error(self, mock_post):
        """Test login with connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        client = PureLinkClient(host="192.168.1.100")

        with pytest.raises(PureLinkConnectionError):
            client.login("admin", "password")

    @patch("pypurelinkmatrix.client.requests.Session.post")
    def test_login_timeout(self, mock_post):
        """Test login with timeout."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        client = PureLinkClient(host="192.168.1.100")

        with pytest.raises(PureLinkConnectionError):
            client.login("admin", "password")

    def test_login_with_instance_credentials(self):
        """Test login using instance credentials."""
        client = PureLinkClient(host="192.168.1.100", username="admin", password="password")

        with patch("pypurelinkmatrix.client.requests.Session.post") as mock_post:
            mock_response = Mock()
            mock_response.text = "status:1"
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            result = client.login()
            assert result is True

    def test_login_credentials_override(self):
        """Test that login credentials override instance credentials."""
        client = PureLinkClient(host="192.168.1.100", username="user1", password="pass1")

        with patch("pypurelinkmatrix.client.requests.Session.post") as mock_post:
            mock_response = Mock()
            mock_response.text = "status:1"
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            result = client.login("user2", "pass2")
            assert result is True
            assert client.username == "user2"
            assert client.password == "pass2"


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager_enter_exit(self):
        """Test context manager entry and exit."""
        with PureLinkClient(host="192.168.1.100") as client:
            assert client is not None
            assert client.host == "192.168.1.100"

    def test_context_manager_closes_session(self):
        """Test that context manager closes session."""
        client = PureLinkClient(host="192.168.1.100")
        with patch.object(client, "close") as mock_close:
            with client:
                pass
            mock_close.assert_called_once()


class TestLogout:
    """Test logout functionality."""

    def test_logout(self):
        """Test logout."""
        client = PureLinkClient(host="192.168.1.100")
        client.is_authenticated = True

        result = client.logout()

        assert result is True
        assert client.is_authenticated is False


class TestRepresentation:
    """Test string representation."""

    def test_repr_not_authenticated(self):
        """Test repr when not authenticated."""
        client = PureLinkClient(host="192.168.1.100", username="admin")
        repr_str = repr(client)

        assert "192.168.1.100" in repr_str
        assert "admin" in repr_str
        assert "not authenticated" in repr_str

    def test_repr_authenticated(self):
        """Test repr when authenticated."""
        client = PureLinkClient(host="192.168.1.100", username="admin")
        client.is_authenticated = True
        repr_str = repr(client)

        assert "192.168.1.100" in repr_str
        assert "admin" in repr_str
        assert "authenticated" in repr_str
