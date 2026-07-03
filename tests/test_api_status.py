import asyncio
import struct
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pypurelinkmatrix.api.status import StatusAPI
from pypurelinkmatrix.api.status_update_manager import StatusUpdateManager


# Helper for mocking auth response
@pytest.fixture
def mock_auth():
    return AsyncMock()


def create_mock_response(content: bytes):
    response = AsyncMock()
    response.read.return_value = content
    response.raise_for_status = MagicMock()
    # Support async context manager
    response.__aenter__.return_value = response
    return response


def create_binary_payload(blocks: list[bytes]) -> bytes:
    payload = bytearray()
    # 16 bytes for sizes (4 blocks * 4 bytes each)
    for b in blocks:
        payload.extend(struct.pack("<I", len(b)))
    # Blocks
    for b in blocks:
        payload.extend(b)
    return bytes(payload)


# --- Tests for StatusAPI ---


@pytest.mark.asyncio
async def test_status_api_video_routing(mock_auth):
    api = StatusAPI(mock_auth)

    # Block 1 contains video routing
    # block_data: [2, 2, 1, 3] (4 bytes)
    block1 = b"\x02\x02\x01\x03"
    blocks = [b"", block1, b"", b""]
    payload = create_binary_payload(blocks)

    mock_auth.request.return_value = create_mock_response(payload)

    routing = await api.async_get_video_routing()

    assert routing == {"1": 3, "2": 3, "3": 2, "4": 4}
    mock_auth.request.assert_called()


@pytest.mark.asyncio
async def test_status_api_audio_state(mock_auth):
    api = StatusAPI(mock_auth)

    # Block 1 contains audio state
    # 4 bytes video routing, 4 bytes HDMI state, 4 bytes de-embed state
    # HDMI: [1, 1, 0, 0] (1=True, 0=False)
    # De-embed: [0, 0, 1, 0]
    block1 = b"\x01\x01\x01\x01" + b"\x01\x01\x00\x00" + b"\x00\x00\x01\x00"
    blocks = [b"", block1, b"", b""]
    payload = create_binary_payload(blocks)

    mock_auth.request.return_value = create_mock_response(payload)

    audio_state = await api.async_get_audio_output_state()

    assert audio_state["1"] == {"hdmi": True, "de_embed": False}
    assert audio_state["2"] == {"hdmi": True, "de_embed": False}
    assert audio_state["3"] == {"hdmi": False, "de_embed": True}
    assert audio_state["4"] == {"hdmi": False, "de_embed": False}


@pytest.mark.asyncio
async def test_status_api_edid_config(mock_auth):
    api = StatusAPI(mock_auth)

    # Block 1 contains EDID config
    # Routing (4), HDMI (4), De-embed (4), EDID (4)
    # EDID indices: [1, 4, 2, 1]
    block1 = (b"\x01" * 12) + (b"\x00" * 4) + b"\x01\x04\x02\x01"
    blocks = [b"", block1, b"", b""]
    payload = create_binary_payload(blocks)

    mock_auth.request.return_value = create_mock_response(payload)

    edid_config = await api.async_get_edid_configuration()

    assert edid_config["1"]["index"] == 1
    assert edid_config["2"]["index"] == 4
    assert edid_config["3"]["index"] == 2
    assert edid_config["4"]["index"] == 1


@pytest.mark.asyncio
async def test_status_api_port_names(mock_auth):
    api = StatusAPI(mock_auth)

    # Block 3 contains names (512 bytes?)
    # Based on _parse_port_names:
    #  4 inputs (16 bytes each),
    #  4 outputs (16 bytes each),
    #  8 presets (16 bytes each)
    block3 = bytearray(256)
    block3[0:5] = b"Input1\x00"
    block3[16:13] = b"Input2\x00"  # Simple test

    blocks = [b"", b"", b"", bytes(block3)]
    payload = create_binary_payload(blocks)

    mock_auth.request.return_value = create_mock_response(payload)

    port_names = await api.async_get_port_names()
    assert port_names["inputs"]["1"] == "Input2"


# --- Tests for StatusUpdateManager ---


@pytest.mark.asyncio
async def test_status_update_manager_callbacks(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    callback = AsyncMock()
    manager.register_callback(1, callback)

    block1 = b"\x00" * 30  # Enough to pass parsing
    blocks = [b"", block1, b"", b""]
    payload = create_binary_payload(blocks)

    # Mock auth request
    mock_auth.request.return_value = create_mock_response(payload)

    # Trigger one update cycle
    await manager._fetch_and_parse_update()

    callback.assert_called_once()
    assert callback.call_args[0][0] == 1
    assert callback.call_args[0][2] == len(block1)


@pytest.mark.asyncio
async def test_status_update_manager_loop_control(mock_auth):
    manager = StatusUpdateManager(mock_auth)

    # Mock update to do nothing or return immediately
    with patch.object(manager, "_fetch_and_parse_update", new_callable=AsyncMock) as mock_fetch:
        manager.start_updates()
        await asyncio.sleep(0.1)  # Let loop run
        manager.stop_updates()

        assert mock_fetch.called
        assert not manager.is_running()
