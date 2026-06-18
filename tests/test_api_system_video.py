"""Unit tests for SystemAPI and VideoAPI."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pypurelinkmatrix.api.system import SystemAPI
from pypurelinkmatrix.api.video import VideoAPI
from pypurelinkmatrix.exceptions import DeviceError


@pytest.fixture
def mock_auth():
    """Mock PureLinkAuth."""
    auth = MagicMock()
    # This needs to be an AsyncMock so it can be awaited
    mock_request = AsyncMock()
    # Configure the response for the async with
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    # The return value of await self.auth.request(...)
    mock_request.return_value.__aenter__.return_value = mock_response
    auth.request = mock_request
    return auth


@pytest.fixture
def mock_state():
    """Mock DeviceState."""
    state = MagicMock()
    state.video = MagicMock()
    return state


@pytest.mark.asyncio
class TestSystemAPI:
    """Tests for SystemAPI."""

    async def test_async_reboot(self, mock_auth):
        """Test reboot command."""
        api = SystemAPI(mock_auth)
        assert await api.async_reboot() is True
        mock_auth.request.assert_called_with("POST", "system_set", data="#power start=1")

    async def test_async_reboot_failure(self, mock_auth):
        """Test reboot command failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = SystemAPI(mock_auth)
        with pytest.raises(DeviceError, match="Reboot command failed"):
            await api.async_reboot()

    async def test_async_factory_reset_common(self, mock_auth):
        """Test common factory reset."""
        api = SystemAPI(mock_auth)
        assert await api.async_factory_reset_common() is True
        mock_auth.request.assert_called_with("POST", "system_set", data="#factory0")

    async def test_async_factory_reset_all(self, mock_auth):
        """Test complete factory reset."""
        api = SystemAPI(mock_auth)
        assert await api.async_factory_reset_all() is True
        mock_auth.request.assert_called_with("POST", "system_set", data="#factory1")

    async def test_async_factory_reset_failure(self, mock_auth):
        """Test factory reset failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = SystemAPI(mock_auth)
        with pytest.raises(DeviceError, match="Factory reset failed"):
            await api.async_factory_reset_common()

    async def test_async_factory_reset_all_failure(self, mock_auth):
        """Test complete factory reset failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = SystemAPI(mock_auth)
        with pytest.raises(DeviceError, match="Complete factory reset failed"):
            await api.async_factory_reset_all()

    async def test_async_change_password(self, mock_auth):
        """Test password change."""
        api = SystemAPI(mock_auth)
        assert await api.async_change_password("admin", "newpass123") is True
        mock_auth.request.assert_called_with(
            "POST", "system_set", data="#register255 id=admin psd=newpass123"
        )

    @pytest.mark.parametrize(
        "username,password,match",
        [
            ("", "pass", "Username must be a non-empty string"),
            ("admin", "", "Password must be a non-empty string"),
            ("a" * 16, "pass", "15 characters or less"),
            ("admin", "p" * 16, "15 characters or less"),
            ("admin!", "pass", "only letters, numbers, and underscores"),
            ("admin", "pass!", "only letters, numbers, and underscores"),
        ],
    )
    async def test_async_change_password_validation(self, mock_auth, username, password, match):
        """Test password change validation."""
        api = SystemAPI(mock_auth)
        with pytest.raises(ValueError, match=match):
            await api.async_change_password(username, password)

    async def test_async_change_password_failure(self, mock_auth):
        """Test password change failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = SystemAPI(mock_auth)
        with pytest.raises(DeviceError, match="Password change failed"):
            await api.async_change_password("admin", "pass")


@pytest.mark.asyncio
class TestVideoAPI:
    """Tests for VideoAPI."""

    async def test_async_switch_matrix(self, mock_auth):
        """Test matrix switching."""
        api = VideoAPI(mock_auth)
        assert await api.async_switch_matrix(1, 2) is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#video_d out1 matrix=2")

    async def test_async_switch_matrix_all_outputs(self, mock_auth):
        """Test matrix switching for all outputs."""
        api = VideoAPI(mock_auth)
        assert await api.async_switch_matrix(0, 3) is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#video_d out256 matrix=3")

    async def test_async_switch_matrix_validation(self, mock_auth):
        """Test matrix switching validation."""
        api = VideoAPI(mock_auth)
        with pytest.raises(ValueError, match="Output must be 0"):
            await api.async_switch_matrix(5, 1)
        with pytest.raises(ValueError, match="Input port must be 1-4"):
            await api.async_switch_matrix(1, 5)

    async def test_async_switch_matrix_with_state(self, mock_auth, mock_state):
        """Test matrix switching with state update."""
        api = VideoAPI(mock_auth, state=mock_state)
        await api.async_switch_matrix(1, 2)
        mock_state.video._set_output_input.assert_called_with(1, 2)

    async def test_async_switch_matrix_all_outputs_with_state(self, mock_auth, mock_state):
        """Test matrix switching for all outputs with state update."""
        api = VideoAPI(mock_auth, state=mock_state)
        await api.async_switch_matrix(0, 3)
        assert mock_state.video._set_output_input.call_count == 4

    async def test_async_switch_matrix_failure(self, mock_auth):
        """Test matrix switching failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = VideoAPI(mock_auth)
        with pytest.raises(DeviceError, match="Matrix switch failed"):
            await api.async_switch_matrix(1, 1)

    async def test_async_save_preset(self, mock_auth):
        """Test saving preset."""
        api = VideoAPI(mock_auth)
        assert await api.async_save_preset(1) is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#preset:1 exe=1")

    async def test_async_save_preset_validation(self, mock_auth):
        """Test saving preset validation."""
        api = VideoAPI(mock_auth)
        with pytest.raises(ValueError, match="Preset number must be 1-8"):
            await api.async_save_preset(0)
        with pytest.raises(ValueError, match="Preset number must be 1-8"):
            await api.async_save_preset(9)

    async def test_async_save_preset_failure(self, mock_auth):
        """Test saving preset failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = VideoAPI(mock_auth)
        with pytest.raises(DeviceError, match="Preset save failed"):
            await api.async_save_preset(1)

    async def test_async_recall_preset(self, mock_auth):
        """Test recalling preset."""
        api = VideoAPI(mock_auth)
        assert await api.async_recall_preset(1) is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#preset:1 exe=0")

    async def test_async_recall_preset_validation(self, mock_auth):
        """Test recalling preset validation."""
        api = VideoAPI(mock_auth)
        with pytest.raises(ValueError, match="Preset number must be 1-8"):
            await api.async_recall_preset(9)

    async def test_async_recall_preset_failure(self, mock_auth):
        """Test recalling preset failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = VideoAPI(mock_auth)
        with pytest.raises(DeviceError, match="Preset recall failed"):
            await api.async_recall_preset(1)

    async def test_async_rename_input(self, mock_auth):
        """Test renaming input."""
        api = VideoAPI(mock_auth)
        assert await api.async_rename_input(1, "Cam1") is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#name0 str=Cam1")

    async def test_async_rename_output(self, mock_auth):
        """Test renaming output."""
        api = VideoAPI(mock_auth)
        assert await api.async_rename_output(1, "Disp1") is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#name4 str=Disp1")

    async def test_async_rename_preset(self, mock_auth):
        """Test renaming preset."""
        api = VideoAPI(mock_auth)
        assert await api.async_rename_preset(1, "Conf") is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#name8 str=Conf")

    async def test_async_rename_input_validation(self, mock_auth):
        """Test rename input validation."""
        api = VideoAPI(mock_auth)
        with pytest.raises(ValueError, match="Input number must be 1-4"):
            await api.async_rename_input(5, "valid_name")

    async def test_async_rename_output_validation(self, mock_auth):
        """Test rename output validation."""
        api = VideoAPI(mock_auth)
        with pytest.raises(ValueError, match="Output number must be 1-4"):
            await api.async_rename_output(5, "valid_name")

    async def test_async_rename_preset_validation(self, mock_auth):
        """Test rename preset validation."""
        api = VideoAPI(mock_auth)
        with pytest.raises(ValueError, match="Preset number must be 1-8"):
            await api.async_rename_preset(9, "valid_name")

    @pytest.mark.parametrize(
        "rename_func", ["async_rename_input", "async_rename_output", "async_rename_preset"]
    )
    @pytest.mark.parametrize(
        "name,match",
        [
            ("", "Name must be a non-empty string"),
            ("thisnameiswaytoolong", "Name must be 15 characters or less"),
            ("invalid-name!", "only letters, numbers, and underscores"),
        ],
    )
    async def test_async_rename_validation(self, mock_auth, rename_func, name, match):
        """Test rename validation."""
        api = VideoAPI(mock_auth)
        func = getattr(api, rename_func)
        with pytest.raises(ValueError, match=match):
            await func(1, name)

    async def test_async_rename_failure(self, mock_auth):
        """Test rename failure."""
        mock_auth.request.return_value.__aenter__.return_value.raise_for_status.side_effect = (
            Exception("error")
        )
        api = VideoAPI(mock_auth)
        with pytest.raises(DeviceError, match="Input rename failed"):
            await api.async_rename_input(1, "valid_name")
