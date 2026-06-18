import asyncio
import struct
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pypurelinkmatrix.api.data_structures import WebInfo
from pypurelinkmatrix.api.status_update_manager import StatusUpdateManager


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


@pytest.mark.asyncio
async def test_unregister_callback(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    callback = MagicMock()

    # Valid registration and unregistration
    manager.register_callback(0, callback)
    assert callback in manager._callbacks[0]
    manager.unregister_callback(0, callback)
    assert callback not in manager._callbacks[0]

    # Test invalid block or non-existent callback (should not fail)
    manager.unregister_callback(5, callback)
    manager.unregister_callback(0, callback)


@pytest.mark.asyncio
async def test_update_loop_exception(mock_auth):
    manager = StatusUpdateManager(mock_auth)

    # We want to trigger the exception block in _update_loop
    # while self._update_is_on: ... except Exception as e: ...

    # Start updates
    manager.start_updates()

    # Mock _fetch_and_parse_update to raise an exception
    with patch.object(manager, "_fetch_and_parse_update", side_effect=Exception("Loop error")):
        # Let it run for a very short time
        await asyncio.sleep(0.01)
        manager.stop_updates()

    # Wait for the task to finish to avoid "Task was destroyed but it is pending"
    if manager._update_task:
        try:
            await manager._update_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_fetch_and_parse_update_empty_response(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    mock_auth.request.return_value = create_mock_response(b"")

    await manager._fetch_and_parse_update()
    # Verification is that it doesn't crash and returns early


@pytest.mark.asyncio
async def test_fetch_and_parse_update_exception(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    mock_auth.request.side_effect = Exception("Fetch error")

    # Should catch exception internally and log it (we check it doesn't raise)
    await manager._fetch_and_parse_update()


@pytest.mark.asyncio
async def test_parse_data_short_data(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    await manager._parse_data(b"too short")
    # Returns early


@pytest.mark.asyncio
async def test_parse_data_adaptive_timing(mock_auth):
    manager = StatusUpdateManager(mock_auth)

    # Test fresh_count > 50
    manager.fresh_count = 51
    payload = create_binary_payload([b"\x00" * 32, b"", b"", b""])
    await manager._parse_data(payload)
    assert manager.fresh_time == 800

    # Test fresh_count > 200
    manager.fresh_count = 201
    await manager._parse_data(payload)
    assert manager.fresh_time == 3000


@pytest.mark.asyncio
async def test_judgment_data_block_callback_error(mock_auth):
    manager = StatusUpdateManager(mock_auth)

    # Mock callback that fails (sync)
    callback_sync = MagicMock(side_effect=Exception("Sync callback error"))
    manager.register_callback(0, callback_sync)

    # Mock callback that fails (async)
    callback_async = AsyncMock(side_effect=Exception("Async callback error"))
    manager.register_callback(0, callback_async)

    await manager._judgment_data_block(b"data", 0, 4, 0)

    callback_sync.assert_called_once()
    callback_async.assert_called_once()


@pytest.mark.asyncio
async def test_judgment_data_block_parser_error(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    with patch.object(manager, "_parse_data_block_0", side_effect=Exception("Parser error")):
        await manager._judgment_data_block(b"data", 0, 4, 0)
        # Should not raise exception


@pytest.mark.asyncio
async def test_parse_data_block_0_parsing(mock_auth):
    manager = StatusUpdateManager(mock_auth)

    # Block 0: IP data (23 bytes minimum)
    data = bytearray([1])  # dhcp = 1
    data.extend([192, 168, 1, 10])  # ip
    data.extend([255, 255, 255, 0])  # mask
    data.extend([192, 168, 1, 1])  # gw
    data.extend([8, 8, 8, 8])  # dns
    data.extend([0x00, 0x11, 0x22, 0x33, 0x44, 0x55])  # mac

    manager._parse_data_block_0(bytes(data), 0, len(data))

    assert manager.web_data.ip.dhcp == 1
    assert manager.web_data.ip.ip == "192.168.1.10"
    assert manager.web_data.ip.mask == "255.255.255.0"
    assert manager.web_data.ip.gw == "192.168.1.1"
    assert manager.web_data.ip.dns == "8.8.8.8"
    assert manager.web_data.ip.mac == "00:11:22:33:44:55"

    # Test short data
    manager._parse_data_block_0(b"short", 0, 5)


@pytest.mark.asyncio
async def test_parse_data_block_1_detailed(mock_auth):
    manager = StatusUpdateManager(mock_auth)

    # Block 1: Runtime state
    # video_mx(4), video_nf(4), audio_hdmi(4), audio_dec(4), edid_mdf(16), edid_cfg(84)
    # total around 116 bytes + status (36 bytes) = 152 bytes

    data_len = 200
    data = bytearray(data_len)
    # Fill with some data
    data[0:4] = b"\x01\x02\x03\x00"  # video_mx

    # edid_cfg starts at 4+4+4+4 + 16 = 32
    # Set some bits to test edid_inf logic
    data[32 + 5] = 1  # edid_inf[0] should be 5
    data[32 + 21 + 10] = 1  # edid_inf[1] should be 10

    # in_port_status/out_port_status
    # start_g_ch = start_addr + data_length - 36
    # For data_length = 200, start_addr = 0, start_g_ch = 164
    data[164] = 1  # in_port_status[0]
    data[164 + 8] = 1  # in_port_status[1]
    data[164 + 32] = 1  # out_port_status[0]

    manager._parse_data_block_1(bytes(data), 0, data_len)

    assert manager.web_data.run.video_mx[0] == 1
    assert manager.web_data.run.edid_inf[0] == 5
    assert manager.web_data.run.edid_inf[1] == 10
    assert manager.web_data.run.in_port_status[0] == 1
    assert manager.web_data.run.out_port_status[0] == 1

    # Test short data
    manager._parse_data_block_1(b"short", 0, 5)


@pytest.mark.asyncio
async def test_parse_data_block_2_edid_strings(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    # Block 2: 21 * 64 bytes
    data = bytearray(1400)
    data[0:10] = b"EDID 1\x00\x00\x00\x00"
    data[64:74] = b"EDID 2\x00\x00\x00\x00"

    manager._parse_data_block_2(bytes(data), 0, len(data))
    assert manager.web_data.name.edid_info[0] == "EDID 1"
    assert manager.web_data.name.edid_info[1] == "EDID 2"


@pytest.mark.asyncio
async def test_parse_data_block_3_names(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    # Block 3: Port/Preset names
    data = bytearray(256)
    data[0:6] = b"In 1\x00\x00"
    data[16:22] = b"In 2\x00\x00"
    data[128:134] = b"Pre 1\x00\x00"

    manager._parse_data_block_3(bytes(data), 0, len(data))
    assert manager.web_data.name.port_name[0] == "In 1"
    assert manager.web_data.name.port_name[1] == "In 2"
    assert manager.web_data.name.preset_name[0] == "Pre 1"


@pytest.mark.asyncio
async def test_async_get_state(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    state = await manager.async_get_state()
    assert isinstance(state, WebInfo)
    assert state is not manager.web_data


@pytest.mark.asyncio
async def test_judgment_data_block_routing(mock_auth):
    manager = StatusUpdateManager(mock_auth)
    with (
        patch.object(manager, "_parse_data_block_0") as p0,
        patch.object(manager, "_parse_data_block_1") as p1,
        patch.object(manager, "_parse_data_block_2") as p2,
        patch.object(manager, "_parse_data_block_3") as p3,
    ):

        await manager._judgment_data_block(b"data", 0, 4, 0)
        p0.assert_called_once()

        await manager._judgment_data_block(b"data", 0, 4, 1)
        p1.assert_called_once()

        await manager._judgment_data_block(b"data", 0, 4, 2)
        p2.assert_called_once()

        await manager._judgment_data_block(b"data", 0, 4, 3)
        p3.assert_called_once()
