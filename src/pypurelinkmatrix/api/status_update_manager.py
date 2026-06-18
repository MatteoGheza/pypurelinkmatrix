"""Status update manager following the JavaScript pattern (Async)."""

import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Optional

from .data_structures import WebInfo
from .status import calculate_crc32

if TYPE_CHECKING:
    from ..auth import PureLinkAuth

logger = logging.getLogger(__name__)

# Type alias for update callbacks
UpdateCallback = Callable[[int, bytes, int], None]  # (block_num, data, size)


class StatusUpdateManager:
    """Manages periodic device status updates with change detection (Async)."""

    def __init__(
        self,
        auth: "PureLinkAuth",
        initial_fresh_time: int = 800,
    ):
        """Initialize the status update manager.

        Args:
            auth: PureLinkAuth instance for HTTP communication
            initial_fresh_time: Initial refresh interval in milliseconds
        """
        self.auth = auth

        # Data block tracking (mirroring JS globals)
        self.data_crc = ["12345678"] * 4  # Initial CRC values - dummy to force first fetch
        self.data_size = [0, 0, 0, 0]

        # Refresh timing (adaptive like JS code)
        self.fresh_time = initial_fresh_time  # Milliseconds (800ms default)
        self.fresh_count = 0  # Number of successful updates

        # Device data container
        self.web_data = WebInfo()

        # Update task management
        self._update_task: Optional[asyncio.Task] = None
        self._update_lock = asyncio.Lock()

        # Callbacks for data block updates
        self._callbacks: dict[int, list[UpdateCallback]] = {0: [], 1: [], 2: [], 3: []}

        # Flag to track if updates are active
        self._update_is_on = False

    def register_callback(self, block_num: int, callback: UpdateCallback) -> None:
        """Register a callback for data block updates."""
        if 0 <= block_num <= 3:
            self._callbacks[block_num].append(callback)
            logger.debug(f"Registered callback for data block {block_num}")

    def unregister_callback(self, block_num: int, callback: UpdateCallback) -> None:
        """Unregister a callback for data block updates."""
        if 0 <= block_num <= 3 and callback in self._callbacks[block_num]:
            self._callbacks[block_num].remove(callback)
            logger.debug(f"Unregistered callback for data block {block_num}")

    def start_updates(self) -> None:
        """Start the periodic status update loop."""
        if not self._update_is_on:
            self._update_is_on = True
            self._update_task = asyncio.create_task(self._update_loop())
            logger.info("Status updates started")

    def stop_updates(self) -> None:
        """Stop the periodic status update loop."""
        self._update_is_on = False
        if self._update_task:
            self._update_task.cancel()
            self._update_task = None
        logger.info("Status updates stopped")

    async def _update_loop(self) -> None:
        """Main update loop."""
        while self._update_is_on:
            try:
                await self._fetch_and_parse_update()

                # Sleep for refresh interval (convert ms to seconds)
                interval = self.fresh_time / 1000.0
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}", exc_info=True)
                await asyncio.sleep(0.5)

    async def _fetch_and_parse_update(self) -> None:
        """Fetch binary data from device and parse update."""
        try:
            # Generate binary endpoint URL with current CRCs
            crc_str = ",".join(self.data_crc)
            endpoint = f"binary{crc_str}.get"

            logger.debug(f"Fetching binary data: {endpoint}")

            # Fetch binary response
            async with await self.auth.request(
                "GET",
                endpoint,
                headers={"Accept": "application/octet-stream"},
            ) as response:
                response.raise_for_status()
                content = await response.read()

            if not content:
                logger.warning("Empty response from binary endpoint")
                return

            # Parse response and process updates
            await self._parse_data(content)

        except Exception as e:
            logger.debug(f"Failed to fetch binary update: {e}")

    async def _parse_data(self, data: bytes) -> None:
        """Parse binary response and route data blocks."""
        if len(data) < 16:
            return

        async with self._update_lock:
            # Increment update counter and adjust timing
            self.fresh_count += 1
            if self.fresh_count > 50 and self.fresh_count < 200:
                self.fresh_time = 2000
            elif self.fresh_count > 200:
                self.fresh_time = 3000

            temp_buf_addr = 16

            for i in range(4):
                offset = i * 4
                size = (
                    (data[offset + 3] << 24)
                    | (data[offset + 2] << 16)
                    | (data[offset + 1] << 8)
                    | (data[offset] & 0xFF)
                )
                self.data_size[i] = size & 0xFFFFFFFF

                temp_buf_end = temp_buf_addr + self.data_size[i]

                if temp_buf_end <= len(data):
                    block_data = data[temp_buf_addr:temp_buf_end]

                    if self.data_size[i] > 0:
                        temp_buf_crc = calculate_crc32(block_data)

                        if self.data_crc[i] != temp_buf_crc:
                            self.fresh_time = 800
                            self.fresh_count = 0
                            self.data_crc[i] = temp_buf_crc

                            logger.debug(
                                f"Data block {i} changed (crc={temp_buf_crc}, "
                                f"size={self.data_size[i]})"
                            )

                            await self._judgment_data_block(
                                block_data,
                                0,
                                self.data_size[i],
                                i,
                            )

                temp_buf_addr = temp_buf_end

    async def _judgment_data_block(
        self,
        data: bytes,
        start_addr: int,
        data_length: int,
        block_num: int,
    ) -> None:
        """Route data block to appropriate parser."""
        logger.debug(f"JudgmentDataBlock: block {block_num}, len {data_length}")

        try:
            if block_num == 0:
                self._parse_data_block_0(data, start_addr, data_length)
            elif block_num == 1:
                self._parse_data_block_1(data, start_addr, data_length)
            elif block_num == 2:
                self._parse_data_block_2(data, start_addr, data_length)
            elif block_num == 3:
                self._parse_data_block_3(data, start_addr, data_length)

        except Exception as e:
            logger.error(f"Error parsing data block {block_num}: {e}", exc_info=True)

        for callback in self._callbacks[block_num]:
            try:
                # Callbacks might be sync or async
                if asyncio.iscoroutinefunction(callback):
                    await callback(block_num, data, data_length)
                else:
                    callback(block_num, data, data_length)
            except Exception as e:
                logger.error(f"Error in callback for block {block_num}: {e}")

    def _parse_data_block_0(self, data: bytes, start_addr: int, data_length: int) -> None:
        """Parse data block 0: Network/IP configuration."""
        if len(data) < start_addr + 23:
            return

        try:
            start_ip = start_addr
            self.web_data.ip.dhcp = data[start_ip]
            self.web_data.ip.ip = (
                f"{data[start_ip + 1]}.{data[start_ip + 2]}."
                f"{data[start_ip + 3]}.{data[start_ip + 4]}"
            )
            self.web_data.ip.mask = (
                f"{data[start_ip + 5]}.{data[start_ip + 6]}."
                f"{data[start_ip + 7]}.{data[start_ip + 8]}"
            )
            self.web_data.ip.gw = (
                f"{data[start_ip + 9]}.{data[start_ip + 10]}."
                f"{data[start_ip + 11]}.{data[start_ip + 12]}"
            )
            self.web_data.ip.dns = (
                f"{data[start_ip + 13]}.{data[start_ip + 14]}."
                f"{data[start_ip + 15]}.{data[start_ip + 16]}"
            )

            mac_parts = [f"{data[start_ip + 17 + i]:02X}" for i in range(6)]
            self.web_data.ip.mac = ":".join(mac_parts)
        except Exception as e:  # pragma: no cover
            logger.error(f"Error parsing IP block: {e}")

    def _parse_data_block_1(self, data: bytes, start_addr: int, data_length: int) -> None:
        """Parse data block 1: Runtime state (video/audio/EDID)."""
        if len(data) < start_addr + 8:
            return

        try:
            start_run = start_addr
            start_audio_num = 0

            for i in range(4):
                self.web_data.run.video_mx[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            for i in range(4):
                self.web_data.run.video_nf[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            for i in range(4):
                self.web_data.run.audio_hdmi[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            for i in range(4):
                self.web_data.run.audio_dec[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            for i in range(4):
                self.web_data.run.edid_mdf[i] = (
                    ((data[start_run + start_audio_num + i * 4 + 3] << 24) & 0x3F)
                    | (data[start_run + start_audio_num + i * 4 + 2] << 16)
                    | (data[start_run + start_audio_num + i * 4 + 1] << 8)
                    | (data[start_run + start_audio_num + i * 4 + 0])
                )
            start_audio_num += 4 * 4

            edid_cfg_len = 4 * (4 + 16 + 1)
            for i in range(edid_cfg_len):
                if start_run + start_audio_num + i < len(data):
                    self.web_data.run.edid_cfg[i] = data[start_run + start_audio_num + i] & 0x3F

            for i in range(4):
                self.web_data.run.edid_inf[i] = 0
                for j in range(21):
                    if self.web_data.run.edid_cfg[j + 21 * i] == 1:
                        self.web_data.run.edid_inf[i] = j
                        break

            start_g_ch = start_addr + data_length - 36
            for i in range(4):
                if start_g_ch + 8 * i < len(data):
                    self.web_data.run.in_port_status[i] = data[start_g_ch + 8 * i] & 0x01
            for i in range(4):
                if start_g_ch + 8 * 4 + i < len(data):
                    self.web_data.run.out_port_status[i] = data[start_g_ch + 8 * 4 + i] & 0x01
        except Exception as e:
            logger.error(f"Error parsing runtime block: {e}")

    def _parse_data_block_2(self, data: bytes, start_addr: int, data_length: int) -> None:
        """Parse data block 2: EDID string data."""
        try:
            start_edid = start_addr
            for i in range(21):
                if start_edid + i * 64 + 64 > len(data):  # pragma: no cover
                    break
                edid_bytes = data[start_edid + i * 64 : start_edid + i * 64 + 64]
                edid_str = edid_bytes.split(b"\x00")[0].decode("utf-8", errors="ignore").strip()
                self.web_data.name.edid_info[i] = edid_str
        except Exception as e:  # pragma: no cover
            logger.error(f"Error parsing EDID info block: {e}")

    def _parse_data_block_3(self, data: bytes, start_addr: int, data_length: int) -> None:
        """Parse data block 3: Port and preset names."""
        try:
            start_pos = start_addr
            for i in range(8):
                if start_pos + i * 16 + 16 > len(data):  # pragma: no cover
                    break
                name_bytes = data[start_pos + i * 16 : start_pos + i * 16 + 16]
                name_str = name_bytes.split(b"\x00")[0].decode("utf-8", errors="ignore").strip()
                self.web_data.name.port_name[i] = name_str

            for i in range(8):
                name_offset = start_pos + 128 + i * 16
                if name_offset + 16 > len(data):  # pragma: no cover
                    break
                name_bytes = data[name_offset : name_offset + 16]
                name_str = name_bytes.split(b"\x00")[0].decode("utf-8", errors="ignore").strip()
                self.web_data.name.preset_name[i] = name_str
        except Exception as e:  # pragma: no cover
            logger.error(f"Error parsing names block: {e}")

    async def async_get_state(self) -> WebInfo:
        """Get current device state (Async)."""
        async with self._update_lock:
            from copy import deepcopy

            return deepcopy(self.web_data)

    def is_running(self) -> bool:
        """Check if update loop is running."""
        return bool(self._update_is_on and self._update_task and not self._update_task.done())
