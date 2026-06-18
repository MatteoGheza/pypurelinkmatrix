"""Tests for PureLinkAuth class."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from pypurelinkmatrix.auth import PureLinkAuth
from pypurelinkmatrix.exceptions import AuthenticationError, PureLinkConnectionError


@pytest.mark.asyncio
async def test_auth_request_error():
    """Test general request error."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    auth = PureLinkAuth(mock_session, "127.0.0.1", "admin", "password")
    auth.is_authenticated = True

    # Mock request to raise an exception
    mock_session.request.side_effect = aiohttp.ClientError("General error")

    with pytest.raises(PureLinkConnectionError):
        await auth.request("GET", "test")


@pytest.mark.asyncio
async def test_auth_login_error():
    """Test login connection error."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    auth = PureLinkAuth(mock_session, "127.0.0.1", "admin", "password")

    mock_session.post.side_effect = aiohttp.ClientError("Login failed")

    with pytest.raises(PureLinkConnectionError):
        await auth.login()


@pytest.mark.asyncio
async def test_auth_login_success():
    """Test successful login."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    auth = PureLinkAuth(mock_session, "127.0.0.1", "admin", "password")

    mock_response = AsyncMock()
    mock_response.text.return_value = 'settingsLoginCallback({"status":"1","str":""});'
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__.return_value = mock_response
    mock_session.post.return_value = mock_response

    assert await auth.login() is True
    assert auth.is_authenticated is True


@pytest.mark.asyncio
async def test_auth_login_invalid_credentials():
    """Test invalid credentials."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    auth = PureLinkAuth(mock_session, "127.0.0.1", "admin", "wrong")

    mock_response = AsyncMock()
    mock_response.text.return_value = 'settingsLoginCallback({"status":"0","str":""});'
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__.return_value = mock_response
    mock_session.post.return_value = mock_response

    with pytest.raises(AuthenticationError):
        await auth.login()


@pytest.mark.asyncio
async def test_auth_login_missing_credentials():
    """Test missing credentials."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    auth = PureLinkAuth(mock_session, "127.0.0.1")

    with pytest.raises(AuthenticationError):
        await auth.login()


@pytest.mark.asyncio
async def test_auth_request_logging(caplog):
    """Test request logging."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    auth = PureLinkAuth(mock_session, "127.0.0.1", "admin", "password")

    # Mock request response
    mock_req_resp = AsyncMock()
    mock_req_resp.__aenter__.return_value = mock_req_resp
    mock_session.request = AsyncMock(return_value=mock_req_resp)

    # Mock login response
    mock_login_resp = AsyncMock()
    mock_login_resp.text.return_value = 'settingsLoginCallback({"status":"1","str":""});'
    mock_login_resp.raise_for_status = MagicMock()
    mock_login_resp.__aenter__.return_value = mock_login_resp

    # Mock request response
    mock_req_resp = AsyncMock()
    mock_req_resp.__aenter__.return_value = mock_req_resp

    mock_session.post.return_value = mock_login_resp
    mock_session.request = AsyncMock(return_value=mock_req_resp)

    with caplog.at_level("DEBUG"):
        await auth.request("GET", "test")
        assert "Making GET request to" in caplog.text
