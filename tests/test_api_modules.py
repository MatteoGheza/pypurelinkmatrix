"""Unit tests for PureLink Matrix API modules."""

# mypy: disable-error-code="method-assign"

from unittest.mock import AsyncMock, MagicMock

import pytest
from pypurelinkmatrix.api.audio import AudioAPI
from pypurelinkmatrix.api.edid import EDIDAPI
from pypurelinkmatrix.api.network import NetworkAPI
from pypurelinkmatrix.api.status import StatusAPI
from pypurelinkmatrix.api.system import SystemAPI
from pypurelinkmatrix.api.video import VideoAPI
from pypurelinkmatrix.exceptions import DeviceError


@pytest.fixture
def mock_auth():
    """Mock PureLinkAuth."""
    auth = MagicMock()
    # Mock the request method as an AsyncMock to support await
    auth.request = AsyncMock()
    return auth


def create_mock_response():
    """Create a mock response with a synchronous raise_for_status."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    return mock_response


@pytest.mark.asyncio
class TestVideoAPI:
    """Tests for VideoAPI."""

    async def test_async_switch_matrix(self, mock_auth):
        api = VideoAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_switch_matrix(1, 2) is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#video_d out1 matrix=2")

    async def test_async_save_preset(self, mock_auth):
        api = VideoAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_save_preset(1) is True
        mock_auth.request.assert_called_with("POST", "video_set", data="#preset:1 exe=1")


@pytest.mark.asyncio
class TestAudioAPI:
    """Tests for AudioAPI."""

    async def test_async_set_hdmi_output(self, mock_auth):
        """Test setting HDMI output."""
        api = AudioAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_set_hdmi_output(1, True) is True
        mock_auth.request.assert_called_with("POST", "audio_set", data="#audio_d out1 hdmi=1")

    async def test_async_set_hdmi_output_with_state(self, mock_auth):
        """Test setting HDMI output with state update."""
        mock_state = MagicMock()
        mock_audio_state = MagicMock()
        mock_audio_output = MagicMock()
        mock_state.audio = mock_audio_state
        mock_audio_state.get_output.return_value = mock_audio_output

        api = AudioAPI(mock_auth, state=mock_state)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_hdmi_output(1, True) is True
        assert mock_audio_output.hdmi_enabled is True

    async def test_async_set_de_embed_output(self, mock_auth):
        api = AudioAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_set_de_embed_output(2, False) is True
        mock_auth.request.assert_called_with("POST", "audio_set", data="#audio_d out2 dec=0")

    async def test_async_set_de_embed_output_with_state(self, mock_auth):
        """Test setting de-embed output with state update."""
        mock_state = MagicMock()
        mock_audio_state = MagicMock()
        mock_audio_output = MagicMock()
        mock_state.audio = mock_audio_state
        mock_audio_state.get_output.return_value = mock_audio_output

        api = AudioAPI(mock_auth, state=mock_state)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_de_embed_output(1, True) is True
        assert mock_audio_output.de_embed_enabled is True

    async def test_async_set_de_embed_output_wrong_params(self, mock_auth):
        """Test setting de-embed output with wrong parameters."""
        api = AudioAPI(mock_auth)
        with pytest.raises(ValueError):
            await api.async_set_de_embed_output(99, False)
        with pytest.raises(ValueError):
            await api.async_set_de_embed_output(-1, False)

    async def test_async_set_de_embed_output_all_with_state_de_embed(self, mock_auth):
        """Test setting all outputs de-embed with state update."""
        mock_state = MagicMock()
        mock_audio_output = MagicMock()
        mock_state.audio.get_output.return_value = mock_audio_output

        api = AudioAPI(mock_auth, state=mock_state)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_de_embed_output(0, True) is True
        assert mock_audio_output.de_embed_enabled is True

    async def test_invalid_output(self, mock_auth):
        """Test invalid output port."""
        api = AudioAPI(mock_auth)
        with pytest.raises(ValueError):
            await api.async_set_hdmi_output(99, True)

    async def test_audio_command_error(self, mock_auth):
        """Test audio command error handling."""
        api = AudioAPI(mock_auth)
        mock_response = create_mock_response()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        with pytest.raises(DeviceError):
            await api.async_set_hdmi_output(1, True)

    async def test_async_set_hdmi_output_no_state_output_all(self, mock_auth):
        """Test setting HDMI all outputs without state."""
        api = AudioAPI(mock_auth, state=None)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_hdmi_output(0, True) is True

    async def test_async_set_hdmi_output_with_state_all_outputs(self, mock_auth):
        """Test setting all HDMI outputs with state update."""
        mock_state = MagicMock()
        api = AudioAPI(mock_auth, state=mock_state)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_hdmi_output(0, True) is True
        assert mock_state.audio.get_output.call_count == 4

    async def test_async_set_de_embed_output_error(self, mock_auth):
        """Test setting de-embed output error."""
        api = AudioAPI(mock_auth)
        mock_response = create_mock_response()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        with pytest.raises(DeviceError):
            await api.async_set_de_embed_output(2, False)


@pytest.mark.asyncio
class TestNetworkAPI:
    """Tests for NetworkAPI."""

    async def test_async_configure_static_ip(self, mock_auth):
        api = NetworkAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert (
            await api.async_configure_static_ip("192.168.1.100", "255.255.255.0", "192.168.1.1")
            is True
        )
        mock_auth.request.assert_called()

    async def test_invalid_ip_config(self, mock_auth):
        """Test invalid IP configuration."""
        api = NetworkAPI(mock_auth)
        # IP and gateway on different subnets
        with pytest.raises(ValueError, match="Gateway address must be on the same network"):
            await api.async_configure_static_ip("192.168.1.100", "255.255.255.0", "10.0.0.1")

    async def test_invalid_ip_format(self, mock_auth):
        """Test invalid IP format."""
        api = NetworkAPI(mock_auth)
        with pytest.raises(ValueError, match="IP address format is invalid"):
            await api.async_configure_static_ip("192.168.1.300", "255.255.255.0", "192.168.1.1")

    async def test_async_enable_dhcp(self, mock_auth):
        api = NetworkAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_enable_dhcp() is True
        mock_auth.request.assert_called_with("POST", "ip.set", data="#ip dhcp=0")

    async def test_async_disable_dhcp(self, mock_auth):
        api = NetworkAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_disable_dhcp() is True
        mock_auth.request.assert_called_with("POST", "ip.set", data="#ip dhcp=1")

    async def test_async_configure_static_ip_failure(self, mock_auth):
        api = NetworkAPI(mock_auth)
        mock_response = create_mock_response()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        with pytest.raises(DeviceError, match="Static IP configuration failed"):
            await api.async_configure_static_ip("192.168.1.100", "255.255.255.0", "192.168.1.1")

    async def test_async_set_dhcp_failure(self, mock_auth):
        api = NetworkAPI(mock_auth)
        mock_response = create_mock_response()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        with pytest.raises(DeviceError, match="DHCP configuration failed"):
            await api.async_enable_dhcp()

    async def test_invalid_ip_type(self, mock_auth):
        api = NetworkAPI(mock_auth)
        with pytest.raises(ValueError, match="IP address must be a non-empty string"):
            await api.async_configure_static_ip(None, "255.255.255.0", "192.168.1.1")  # type: ignore
        with pytest.raises(ValueError, match="IP address must be a non-empty string"):
            await api.async_configure_static_ip("", "255.255.255.0", "192.168.1.1")


@pytest.mark.asyncio
class TestSystemAPI:
    """Tests for SystemAPI."""

    async def test_async_factory_reset_common(self, mock_auth):
        api = SystemAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_factory_reset_common() is True
        mock_auth.request.assert_called_with("POST", "system_set", data="#factory0")

    async def test_async_factory_reset_all(self, mock_auth):
        api = SystemAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_factory_reset_all() is True
        mock_auth.request.assert_called_with("POST", "system_set", data="#factory1")

    async def test_async_change_password(self, mock_auth):
        api = SystemAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_change_password("admin", "newpass") is True

    async def test_invalid_password(self, mock_auth):
        api = SystemAPI(mock_auth)
        with pytest.raises(ValueError):
            await api.async_change_password("admin", "invalid!@#")


@pytest.mark.asyncio
class TestEDIDAPI:
    """Tests for EDIDAPI."""

    async def test_async_set_input_edid(self, mock_auth):
        api = EDIDAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response
        assert await api.async_set_input_edid(1, 2) is True
        mock_auth.request.assert_called_with("POST", "input.set", data="#edid in1 cfg=0/2")

    async def test_async_set_input_edid_with_state(self, mock_auth):
        """Test setting input EDID with state update."""
        mock_state = MagicMock()
        api = EDIDAPI(mock_auth, state=mock_state)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_input_edid(1, 1) is True
        mock_state.edid._set_input_edid.assert_called_with(1, 1)

    async def test_async_set_input_edid_all_with_state(self, mock_auth):
        """Test setting all inputs EDID with state update."""
        mock_state = MagicMock()
        api = EDIDAPI(mock_auth, state=mock_state)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_input_edid(0, 1) is True
        assert mock_state.edid._set_input_edid.call_count == 4

    async def test_async_set_input_edid_invalid_input(self, mock_auth):
        """Test invalid input number for set_input_edid."""
        api = EDIDAPI(mock_auth)
        with pytest.raises(ValueError, match="Input number must be 0"):
            await api.async_set_input_edid(5, 1)

    async def test_async_set_input_edid_error(self, mock_auth):
        """Test error handling in set_input_edid."""
        api = EDIDAPI(mock_auth)
        mock_auth.request.side_effect = Exception("error")
        with pytest.raises(DeviceError, match="Input EDID configuration failed"):
            await api.async_set_input_edid(1, 1)

    async def test_async_set_user_edid_success(self, mock_auth):
        """Test setting user EDID successfully."""
        api = EDIDAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_user_edid(1, 1) is True
        mock_auth.request.assert_called_with("POST", "input.set", data="#edid user1 cfg=0/1")

    async def test_async_set_user_edid_all(self, mock_auth):
        """Test setting all user EDID slots."""
        api = EDIDAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_set_user_edid(1, 0) is True
        mock_auth.request.assert_called_with("POST", "input.set", data="#edid user0 cfg=0/1")

    async def test_async_set_user_edid_invalid_source_profile(self, mock_auth):
        """Test invalid source profile for set_user_edid."""
        api = EDIDAPI(mock_auth)
        with pytest.raises(ValueError, match="Source profile must be 1-17"):
            await api.async_set_user_edid(18, 1)

    async def test_async_set_user_edid_error(self, mock_auth):
        """Test error handling in set_user_edid."""
        api = EDIDAPI(mock_auth)
        mock_auth.request.side_effect = Exception("error")
        with pytest.raises(DeviceError, match="User EDID configuration failed"):
            await api.async_set_user_edid(1, 1)

    async def test_get_edid_type_and_index(self, mock_auth):
        """Test internal _get_edid_type_and_index method."""
        api = EDIDAPI(mock_auth)
        # Default
        assert api._get_edid_type_and_index(1) == (0, 1)
        # User
        assert api._get_edid_type_and_index(9) == (1, 1)
        # Output
        assert api._get_edid_type_and_index(13) == (2, 1)
        # Temp
        assert api._get_edid_type_and_index(17) == (4, 1)

    async def test_async_rename_input_port_invalid_input(self, mock_auth):
        """Test invalid input number for rename_input_port."""
        api = EDIDAPI(mock_auth)
        with pytest.raises(ValueError, match="Input number must be 1-4"):
            await api.async_rename_input_port(5, "Name")

    async def test_async_rename_input_port_error(self, mock_auth):
        """Test error handling in rename_input_port."""
        api = EDIDAPI(mock_auth)
        mock_auth.request.side_effect = Exception("error")
        with pytest.raises(DeviceError, match="Input port rename failed"):
            await api.async_rename_input_port(1, "Name")

    async def test_validate_name_edge_cases(self, mock_auth):
        """Test name validation edge cases."""
        api = EDIDAPI(mock_auth)
        # Empty
        with pytest.raises(ValueError, match="non-empty string"):
            api._validate_name("")
        # Not string
        with pytest.raises(ValueError, match="non-empty string"):
            api._validate_name(None)  # type: ignore
        # Too long
        with pytest.raises(ValueError, match="15 characters or less"):
            api._validate_name("a" * 16)
        # Invalid characters
        with pytest.raises(ValueError, match="only letters, numbers"):
            api._validate_name("Invalid!")

    async def test_async_rename_input_port(self, mock_auth):
        """Test renaming input port."""
        api = EDIDAPI(mock_auth)
        mock_response = create_mock_response()
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        assert await api.async_rename_input_port(1, "Camera1") is True
        mock_auth.request.assert_called_with("POST", "input.set", data="#name0 str=Camera1")

    async def test_rename_input_port_invalid_name(self, mock_auth):
        """Test renaming input port with invalid name."""
        api = EDIDAPI(mock_auth)
        with pytest.raises(ValueError):
            await api.async_rename_input_port(1, "Invalid Name!")

    async def test_async_set_input_edid_invalid_source(self, mock_auth):
        """Test invalid EDID source."""
        api = EDIDAPI(mock_auth)
        with pytest.raises(ValueError):
            await api.async_set_input_edid(1, 99)

    async def test_async_set_user_edid_invalid_destination(self, mock_auth):
        """Test invalid user EDID destination."""
        api = EDIDAPI(mock_auth)
        with pytest.raises(ValueError):
            await api.async_set_user_edid(1, 99)


@pytest.mark.asyncio
class TestStatusAPI:
    """Tests for StatusAPI."""

    async def test_async_get_audio_output_state(self, mock_auth):
        """Test getting audio output state."""
        api = StatusAPI(mock_auth)

        # Header + Data block 1 (size >= 12 bytes for audio)
        data = (
            b"\x00\x00\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00" * 4
            + b"\x01\x01\x01\x01"
            + b"\x00\x00\x00\x00"
        )

        mock_response = create_mock_response()
        mock_response.read.return_value = data
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        audio_state = await api.async_get_audio_output_state()
        assert audio_state["1"]["hdmi"] is True
        assert audio_state["1"]["de_embed"] is False

    async def test_async_get_edid_configuration(self, mock_auth):
        """Test getting EDID configuration."""
        api = StatusAPI(mock_auth)

        # Header + Data block 1 (size >= 20 bytes for EDID)
        data = (
            b"\x00\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\x00" * 16
            + b"\x00\x01\x02\x03"
        )

        mock_response = create_mock_response()
        mock_response.read.return_value = data
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        edid_config = await api.async_get_edid_configuration()
        assert edid_config["1"]["name"] == "Default1"
        assert edid_config["2"]["name"] == "Default2"
        assert edid_config["3"]["name"] == "Default3"
        assert edid_config["4"]["name"] == "Default4"

    async def test_status_api_crc32_empty(self, mock_auth):
        """Test CRC32 with empty data."""
        from pypurelinkmatrix.api.status import calculate_crc32

        assert calculate_crc32(b"") == "ffffffff"

    async def test_status_api_binary_response_too_short(self, mock_auth):
        """Test binary response too short."""
        api = StatusAPI(mock_auth)
        api._parse_binary_response(b"\x00" * 15)
        assert api.data_size[0] == 0

    async def test_status_api_get_video_routing_empty_response(self, mock_auth):
        """Test video routing with empty response."""
        api = StatusAPI(mock_auth)
        mock_response = create_mock_response()
        mock_response.read.return_value = b""
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        routing = await api.async_get_video_routing()
        assert routing == {"1": 1, "2": 1, "3": 1, "4": 1}

    async def test_status_api_get_video_routing_error(self, mock_auth):
        """Test video routing with request error."""
        api = StatusAPI(mock_auth)
        mock_auth.request.side_effect = Exception("error")
        routing = await api.async_get_video_routing()
        assert routing == {"1": 1, "2": 1, "3": 1, "4": 1}

    async def test_status_api_get_audio_state_error(self, mock_auth):
        """Test audio state with request error."""
        api = StatusAPI(mock_auth)
        mock_auth.request.side_effect = Exception("error")
        state = await api.async_get_audio_output_state()
        assert state["1"]["hdmi"] is True

    async def test_status_api_get_edid_config_error(self, mock_auth):
        """Test EDID config with request error."""
        api = StatusAPI(mock_auth)
        mock_auth.request.side_effect = Exception("error")
        config = await api.async_get_edid_configuration()
        assert config["1"]["name"] == "Default1"

    async def test_status_api_get_port_names_error(self, mock_auth):
        """Test port names with request error."""
        api = StatusAPI(mock_auth)
        mock_auth.request.side_effect = Exception("error")
        names = await api.async_get_port_names()
        assert names["inputs"]["1"] == "Input_1"

    async def test_status_api_get_full_status_success(self, mock_auth):
        """Test getting full status successfully."""
        api = StatusAPI(mock_auth)

        # Mocking individual calls to avoid complex binary data setup
        api.async_get_video_routing = AsyncMock(return_value={"1": 1})
        api.async_get_audio_output_state = AsyncMock(return_value={"1": {"hdmi": True}})
        api.async_get_edid_configuration = AsyncMock(return_value={"1": {"name": "Default1"}})
        api.async_get_port_names = AsyncMock(return_value={"inputs": {"1": "Input1"}})

        status = await api.async_get_full_status()
        assert status["video_routing"] == {"1": 1}
        assert status["audio_state"] == {"1": {"hdmi": True}}

    async def test_status_api_get_full_status_error(self, mock_auth):
        """Test getting full status with error."""
        api = StatusAPI(mock_auth)
        api.async_get_video_routing = AsyncMock(side_effect=Exception("error"))
        with pytest.raises(DeviceError):
            await api.async_get_full_status()

    async def test_status_api_crc32_with_data(self, mock_auth):
        """Test CRC32 with specific data to cover all branches."""
        from pypurelinkmatrix.api.status import calculate_crc32

        # Data not multiple of 4 to cover remaining bytes logic
        data = b"12345"
        crc = calculate_crc32(data)
        assert len(crc) == 8

        # Test _crc32_get branches by using data that triggers them
        # (difficult to target specific bits but 0xFF should do something)
        assert calculate_crc32(b"\xff\xff\xff\xff") != "ffffffff"

    async def test_status_api_get_video_routing_success(self, mock_auth):
        """Test video routing success with valid binary data."""
        api = StatusAPI(mock_auth)
        # Header (16 bytes) + Block 0 (0) + Block 1 (4 bytes minimum)
        # Block 1 size is at offset 4-7
        data = bytearray(16 + 4)
        data[4] = 4  # Block 1 size = 4
        data[16] = 2  # Output 1 -> Input 2

        mock_response = create_mock_response()
        mock_response.read.return_value = bytes(data)
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        routing = await api.async_get_video_routing()
        assert routing["1"] == 2

    async def test_status_api_get_port_names_success(self, mock_auth):
        """Test port names success with valid binary data."""
        api = StatusAPI(mock_auth)
        # Block 3 size is at offset 12-15. Need at least 256 bytes for block 3.
        # Header (16) + Block 0 + Block 1 + Block 2 + Block 3
        # If block 0,1,2 are size 0.
        data = bytearray(16 + 256)
        data[12] = 0x00
        data[13] = 0x01  # 256 in little-endian (0x0100)

        # Input 1 name at block 3 offset 0
        data[16:19] = b"In1"
        # Output 1 name at block 3 offset 64
        data[16 + 64 : 16 + 64 + 4] = b"Out1"
        # Preset 1 name at block 3 offset 128
        data[16 + 128 : 16 + 128 + 4] = b"Pre1"

        mock_response = create_mock_response()
        mock_response.read.return_value = bytes(data)
        mock_auth.request.return_value.__aenter__.return_value = mock_response

        names = await api.async_get_port_names()
        assert names["inputs"]["1"] == "In1"
        assert names["outputs"]["1"] == "Out1"
        assert names["presets"]["1"] == "Pre1"
