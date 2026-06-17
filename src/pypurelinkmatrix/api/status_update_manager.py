"""Status update manager following the JavaScript pattern.

This module implements the update loop logic from the original JavaScript code,
including CRC-based change detection, adaptive refresh timing, and data block routing.
"""

import logging
import threading
import time
from typing import Callable, Optional

from .data_structures import WebInfo
from .status import calculate_crc32

logger = logging.getLogger(__name__)

# Type alias for update callbacks
UpdateCallback = Callable[[int, bytes, int], None]  # (block_num, data, size)


class StatusUpdateManager:
    """Manages periodic device status updates with change detection.

    Mirrors the JavaScript logic:
    - updateBinary(): Periodic fetch with CRC tracking
    - JudgmentDataBlock(): Route data blocks to appropriate handlers
    - ParseData(): Parse binary response and calculate CRCs
    - Adaptive refresh timing based on change frequency

    Pattern:
    1. Start update loop with start_updates()
    2. Updates fetch binary data every fresh_time milliseconds
    3. Calculate CRC for each data block
    4. Only process blocks with changed CRC
    5. Adaptive timing: slower refresh if no changes, faster if frequent changes
    """

    def __init__(
        self,
        session,
        base_url: str,
        initial_fresh_time: int = 800,
    ):
        """Initialize the status update manager.

        Args:
            session: Requests session for HTTP communication
            base_url: Base URL of the device
            initial_fresh_time: Initial refresh interval in milliseconds
        """
        self.session = session
        self.base_url = base_url

        # Data block tracking (mirroring JS globals)
        self.data_crc = ["12345678"] * 4  # Initial CRC values - dummy to force first fetch
        self.data_size = [0, 0, 0, 0]

        # Refresh timing (adaptive like JS code)
        self.fresh_time = initial_fresh_time  # Milliseconds (800ms default)
        self.fresh_count = 0  # Number of successful updates

        # Device data container
        self.web_data = WebInfo()

        # Update thread management
        self._update_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._update_lock = threading.Lock()

        # Callbacks for data block updates
        self._callbacks: dict[int, list[UpdateCallback]] = {0: [], 1: [], 2: [], 3: []}

        # Flag to track if updates are active
        self._update_is_on = False

    def register_callback(self, block_num: int, callback: UpdateCallback) -> None:
        """Register a callback for data block updates.

        Callbacks are invoked when a data block's CRC changes,
        indicating new data has arrived.

        Args:
            block_num: Data block number (0-3)
            callback: Callable(block_num, data, size) to invoke on update

        Example:
            >>> def on_network_update(block_num, data, size):
            ...     print(f"Block {block_num} updated with {size} bytes")
            >>> manager.register_callback(0, on_network_update)
        """
        if 0 <= block_num <= 3:
            self._callbacks[block_num].append(callback)
            logger.debug(f"Registered callback for data block {block_num}")

    def unregister_callback(self, block_num: int, callback: UpdateCallback) -> None:
        """Unregister a callback for data block updates.

        Args:
            block_num: Data block number (0-3)
            callback: Callback to remove
        """
        if 0 <= block_num <= 3 and callback in self._callbacks[block_num]:
            self._callbacks[block_num].remove(callback)
            logger.debug(f"Unregistered callback for data block {block_num}")

    def start_updates(self) -> None:
        """Start the periodic status update loop.

        Mirrors JavaScript: doBinaryUpdate()
        Starts background thread to continuously fetch binary status data.
        """
        if not self._update_is_on:
            self._update_is_on = True
            self._stop_event.clear()
            self._update_thread = threading.Thread(
                target=self._update_loop, daemon=True, name="StatusUpdateManager"
            )
            self._update_thread.start()
            logger.info("Status updates started")

    def stop_updates(self) -> None:
        """Stop the periodic status update loop.

        Mirrors JavaScript: stopBinaryUpdate()
        """
        self._update_is_on = False
        self._stop_event.set()

        if self._update_thread:
            self._update_thread.join(timeout=5)
            self._update_thread = None

        logger.info("Status updates stopped")

    def _update_loop(self) -> None:
        """Main update loop executed in background thread.

        Mirrors JavaScript updateBinary():
        1. Sleep briefly to allow device processing
        2. Fetch binary data with current CRCs
        3. Parse response and update CRCs
        4. Route data blocks to callbacks
        5. Adjust refresh timing based on change frequency
        """
        while not self._stop_event.is_set():
            try:
                self._fetch_and_parse_update()

                # Sleep for refresh interval (convert ms to seconds)
                interval = self.fresh_time / 1000.0
                self._stop_event.wait(interval)

            except Exception as e:
                logger.error(f"Error in update loop: {e}", exc_info=True)
                # Continue despite errors
                self._stop_event.wait(0.5)

    def _fetch_and_parse_update(self) -> None:
        """Fetch binary data from device and parse update.

        Mirrors JavaScript updateBinary() -> ParseData() flow.
        """
        try:
            # Generate binary endpoint URL with current CRCs
            timestamp = int(time.time() * 1000)
            crc_str = ",".join(self.data_crc)
            endpoint = f"binary{crc_str}.get{timestamp}"
            url = f"{self.base_url}/{endpoint}"

            logger.debug(f"Fetching binary data: {endpoint}")

            # Fetch binary response
            response = self.session.get(
                url,
                timeout=30,
                verify=False,
                headers={"Accept": "application/octet-stream"},
                allow_redirects=True,
            )
            response.raise_for_status()

            if not response.content:
                logger.warning("Empty response from binary endpoint")
                return

            # Parse response and process updates
            self._parse_data(response.content)

        except Exception as e:
            logger.debug(f"Failed to fetch binary update: {e}")

    def _parse_data(self, data: bytes) -> None:
        """Parse binary response and route data blocks.

        Mirrors JavaScript ParseData():
        1. Parse data block sizes from header
        2. Calculate CRC for each block
        3. For blocks with changed CRC, route to JudgmentDataBlock
        4. Adjust refresh timing based on update frequency

        Args:
            data: Raw binary response from device
        """
        if len(data) < 16:
            logger.debug(f"Response too short: {len(data)} bytes")
            return

        with self._update_lock:
            # Increment update counter and adjust timing
            self.fresh_count += 1
            if self.fresh_count > 50 and self.fresh_count < 200:
                self.fresh_time = 2000  # Slow down if many updates
            elif self.fresh_count > 200:
                self.fresh_time = 3000  # Slower after many updates

            # Parse data block sizes (BIG-ENDIAN)
            temp_buf_addr = 16  # Data starts after header

            for i in range(4):
                # Parse size for block i
                offset = i * 4
                size = (
                    (data[offset + 3] << 24)
                    | (data[offset + 2] << 16)
                    | (data[offset + 1] << 8)
                    | (data[offset] & 0xFF)
                )
                self.data_size[i] = size & 0xFFFFFFFF

                # Calculate end position for this block
                temp_buf_end = temp_buf_addr + self.data_size[i]

                # Extract data block
                if temp_buf_end <= len(data):
                    block_data = data[temp_buf_addr:temp_buf_end]

                    # Calculate CRC for this block
                    if self.data_size[i] > 0:
                        temp_buf_crc = calculate_crc32(block_data)

                        # Check if CRC changed (data updated)
                        if self.data_crc[i] != temp_buf_crc:
                            # CRC changed, process this data block
                            self.fresh_time = 800  # Reset to fast updates
                            self.fresh_count = 0
                            self.data_crc[i] = temp_buf_crc

                            logger.debug(
                                f"Data block {i} changed (crc={temp_buf_crc}, "
                                f"size={self.data_size[i]})"
                            )

                            # Route data block to judgment handler
                            self._judgment_data_block(
                                block_data,
                                0,  # start_addr within block
                                self.data_size[i],
                                i,  # block number
                            )
                else:
                    logger.debug(
                        f"Data block {i}: incomplete (need {temp_buf_end}, " f"have {len(data)})"
                    )

                # Move to next block
                temp_buf_addr = temp_buf_end

    def _judgment_data_block(
        self,
        data: bytes,
        start_addr: int,
        data_length: int,
        block_num: int,
    ) -> None:
        """Route data block to appropriate parser based on block number.

        Mirrors JavaScript JudgmentDataBlock():
        - Block 0: Network/IP data
        - Block 1: Video/Audio/EDID runtime state
        - Block 2: EDID string data
        - Block 3: Port/Preset names

        Args:
            data: Data block bytes
            start_addr: Start address within block
            data_length: Data block length
            block_num: Block number (0-3)
        """
        logger.debug(f"JudgmentDataBlock: block {block_num}, len {data_length}")

        try:
            if block_num == 0:
                # Network/IP configuration data
                self._parse_data_block_0(data, start_addr, data_length)
            elif block_num == 1:
                # Video/Audio/EDID runtime state
                self._parse_data_block_1(data, start_addr, data_length)
            elif block_num == 2:
                # EDID string/label data
                self._parse_data_block_2(data, start_addr, data_length)
            elif block_num == 3:
                # Port and preset names
                self._parse_data_block_3(data, start_addr, data_length)

        except Exception as e:
            logger.error(f"Error parsing data block {block_num}: {e}", exc_info=True)

        # Invoke registered callbacks for this block
        for callback in self._callbacks[block_num]:
            try:
                callback(block_num, data, data_length)
            except Exception as e:
                logger.error(f"Error in callback for block {block_num}: {e}")

    def _parse_data_block_0(
        self,
        data: bytes,
        start_addr: int,
        data_length: int,
    ) -> None:
        """Parse data block 0: Network/IP configuration.

        Mirrors JavaScript ParseData0(): IP_INFO_T structure
        """
        if len(data) < start_addr + 23:
            logger.warning("Data block 0 too short for full IP info")
            return

        try:
            start_ip = start_addr

            # DHCP enabled flag
            self.web_data.ip.dhcp = data[start_ip]

            # IP address
            self.web_data.ip.ip = (
                f"{data[start_ip + 1]}.{data[start_ip + 2]}."
                f"{data[start_ip + 3]}.{data[start_ip + 4]}"
            )

            # Subnet mask
            self.web_data.ip.mask = (
                f"{data[start_ip + 5]}.{data[start_ip + 6]}."
                f"{data[start_ip + 7]}.{data[start_ip + 8]}"
            )

            # Gateway
            self.web_data.ip.gw = (
                f"{data[start_ip + 9]}.{data[start_ip + 10]}."
                f"{data[start_ip + 11]}.{data[start_ip + 12]}"
            )

            # DNS
            self.web_data.ip.dns = (
                f"{data[start_ip + 13]}.{data[start_ip + 14]}."
                f"{data[start_ip + 15]}.{data[start_ip + 16]}"
            )

            # MAC address
            mac_parts = []
            for i in range(6):
                hex_val = f"{data[start_ip + 17 + i]:02X}"
                mac_parts.append(hex_val)
            self.web_data.ip.mac = ":".join(mac_parts)

            logger.debug(f"Parsed IP info: {self.web_data.ip.ip}")

        except Exception as e:
            logger.error(f"Error parsing IP block: {e}")

    def _parse_data_block_1(
        self,
        data: bytes,
        start_addr: int,
        data_length: int,
    ) -> None:
        """Parse data block 1: Runtime state (video/audio/EDID).

        Mirrors JavaScript ParseData1(): RUN_INF_T structure
        """
        if len(data) < start_addr + 8:
            logger.warning("Data block 1 too short")
            return

        try:
            start_run = start_addr
            start_audio_num = 0

            # 1. Video matrix routing (4 outputs)
            for i in range(4):
                self.web_data.run.video_mx[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            # 2. Video on/off state (4 outputs)
            for i in range(4):
                self.web_data.run.video_nf[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            # 3. Audio HDMI state (4 outputs)
            for i in range(4):
                self.web_data.run.audio_hdmi[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            # 4. Audio de-embedded state (4 outputs)
            for i in range(4):
                self.web_data.run.audio_dec[i] = data[start_run + start_audio_num + i] & 0x3F
            start_audio_num += 4

            # 5. EDID modification flags (4 x 4-byte values)
            for i in range(4):
                self.web_data.run.edid_mdf[i] = (
                    ((data[start_run + start_audio_num + i * 4 + 3] << 24) & 0x3F)
                    | (data[start_run + start_audio_num + i * 4 + 2] << 16)
                    | (data[start_run + start_audio_num + i * 4 + 1] << 8)
                    | (data[start_run + start_audio_num + i * 4 + 0])
                )
            start_audio_num += 4 * 4

            # 6. EDID configuration (4*(4+16+1) = 84 bytes)
            edid_cfg_len = 4 * (4 + 16 + 1)
            for i in range(edid_cfg_len):
                if start_run + start_audio_num + i < len(data):
                    self.web_data.run.edid_cfg[i] = data[start_run + start_audio_num + i] & 0x3F

            # 7. Determine active EDID for each input
            for i in range(4):
                self.web_data.run.edid_inf[i] = 0
                for j in range(21):
                    if self.web_data.run.edid_cfg[j + 21 * i] == 1:
                        self.web_data.run.edid_inf[i] = j
                        break

            # 8. Port status (from end of block)
            start_g_ch = start_addr + data_length - 36

            # Input port status (4 ports, 8 bytes each)
            for i in range(4):
                if start_g_ch + 8 * i < len(data):
                    self.web_data.run.in_port_status[i] = data[start_g_ch + 8 * i] & 0x01

            # Output port status (4 ports, 1 byte each)
            for i in range(4):
                if start_g_ch + 8 * 4 + i < len(data):
                    self.web_data.run.out_port_status[i] = data[start_g_ch + 8 * 4 + i] & 0x01

            logger.debug(f"Parsed runtime data: video_mx={self.web_data.run.video_mx}")

        except Exception as e:
            logger.error(f"Error parsing runtime block: {e}")

    def _parse_data_block_2(
        self,
        data: bytes,
        start_addr: int,
        data_length: int,
    ) -> None:
        """Parse data block 2: EDID string data.

        Mirrors JavaScript ParseData2(): STRING_INF_T (edid_info)
        """
        try:
            start_edid = start_addr

            # Parse 21 EDID descriptions (64 bytes each)
            for i in range(21):
                if start_edid + i * 64 + 64 > len(data):
                    break

                edid_bytes = data[start_edid + i * 64 : start_edid + i * 64 + 64]

                # Extract null-terminated string
                edid_str = ""
                for byte_val in edid_bytes:
                    if byte_val == 0:
                        break
                    edid_str += chr(byte_val)

                self.web_data.name.edid_info[i] = edid_str

            logger.debug("Parsed EDID info data")

        except Exception as e:
            logger.error(f"Error parsing EDID info block: {e}")

    def _parse_data_block_3(
        self,
        data: bytes,
        start_addr: int,
        data_length: int,
    ) -> None:
        """Parse data block 3: Port and preset names.

        Mirrors JavaScript ParseData3(): STRING_INF_T (port_name, preset_name)
        """
        try:
            start_pos = start_addr

            # Parse port names (8 names, 16 bytes each)
            for i in range(8):
                if start_pos + i * 16 + 16 > len(data):
                    break

                name_bytes = data[start_pos + i * 16 : start_pos + i * 16 + 16]

                # Extract null-terminated string
                name_str = ""
                for byte_val in name_bytes:
                    if byte_val == 0:
                        break
                    name_str += chr(byte_val)

                self.web_data.name.port_name[i] = name_str

            # Parse preset names (8 names, 16 bytes each, start at offset 128)
            for i in range(8):
                name_offset = start_pos + 128 + i * 16
                if name_offset + 16 > len(data):
                    break

                name_bytes = data[name_offset : name_offset + 16]

                # Extract null-terminated string
                name_str = ""
                for byte_val in name_bytes:
                    if byte_val == 0:
                        break
                    name_str += chr(byte_val)

                self.web_data.name.preset_name[i] = name_str

            logger.debug("Parsed port and preset names")

        except Exception as e:
            logger.error(f"Error parsing names block: {e}")

    def get_state(self) -> WebInfo:
        """Get current device state.

        Thread-safe access to the complete device state.

        Returns:
            Current WebInfo state
        """
        with self._update_lock:
            # Return a copy of the state to avoid external modifications
            from copy import deepcopy

            return deepcopy(self.web_data)

    def is_running(self) -> bool:
        """Check if update loop is running.

        Returns:
            True if updates are active
        """
        return bool(self._update_is_on and self._update_thread and self._update_thread.is_alive())
