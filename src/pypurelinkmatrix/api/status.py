"""Device status and state query API."""

import asyncio
import logging
import struct
from typing import TYPE_CHECKING, Any

from ..exceptions import DeviceError

if TYPE_CHECKING:
    from ..auth import PureLinkAuth

logger = logging.getLogger(__name__)


# CRC32 constants
CRC32_POLYNOMIAL = 0x04C11DB7
CRC32_INIT = 0xFFFFFFFF


def _crc32_get(crc: int, dat: int) -> int:
    """Calculate CRC32 for one 32-bit value.

    Args:
        crc: Current CRC value
        dat: Data value to process

    Returns:
        Updated CRC value
    """
    mask = 0x80000000

    while mask:
        if crc & 0x80000000:
            crc = (crc << 1) ^ CRC32_POLYNOMIAL
        else:
            crc = crc << 1

        if dat & mask:
            crc = crc ^ CRC32_POLYNOMIAL

        mask >>= 1

    return crc & 0xFFFFFFFF


def _bytes_to_uint32_array(data: bytes) -> list[int]:
    """Convert bytes to array of 32-bit unsigned integers (little-endian).

    Args:
        data: Byte array to convert

    Returns:
        list of 32-bit unsigned integers
    """
    result = []
    for i in range(0, len(data), 4):
        if i + 4 <= len(data):
            # Little-endian conversion
            val = data[i] | (data[i + 1] << 8) | (data[i + 2] << 16) | (data[i + 3] << 24)
            result.append(val & 0xFFFFFFFF)
        else:
            # Handle remaining bytes
            remaining = len(data) - i
            val = 0
            for j in range(remaining):
                val |= data[i + j] << (j * 8)
            # Pad remaining bytes with 0xFF
            for j in range(remaining, 4):
                val |= 0xFF << (j * 8)
            result.append(val & 0xFFFFFFFF)

    return result


def calculate_crc32(data: bytes) -> str:
    """Calculate CRC32 checksum for byte array.

    Implements the device's CRC32 algorithm used for binary data validation.

    Args:
        data: Byte array to calculate CRC for

    Returns:
        CRC32 value as hexadecimal string
    """
    if not data:
        return "ffffffff"

    crc = CRC32_INIT

    # Convert bytes to 32-bit integers
    uint32_array = _bytes_to_uint32_array(data)

    # Process complete 32-bit words
    num_words = len(data) // 4
    for i in range(num_words):
        crc = _crc32_get(crc, uint32_array[i])

    # Handle remaining bytes
    remaining_bytes = len(data) % 4
    if remaining_bytes > 0:
        remaining_val = 0
        for i in range(remaining_bytes):
            remaining_val |= data[num_words * 4 + i] << (i * 8)
        # Pad with 0xFF
        for i in range(remaining_bytes, 4):
            remaining_val |= 0xFF << (i * 8)
        crc = _crc32_get(crc, remaining_val & 0xFFFFFFFF)

    return f"{crc:08x}"


class StatusAPI:
    """API for querying device status and current state."""

    def __init__(self, auth: "PureLinkAuth"):
        """Initialize status API.

        Args:
            auth: PureLinkAuth instance for HTTP communication
        """
        self.auth = auth
        # Track CRC values for data blocks (initially 0)
        self.data_crc = ["0", "0", "0", "0"]
        # Track data sizes for parsing
        self.data_size = [0, 0, 0, 0]
        # Persistent cache of data blocks
        self.data_blocks = [b"", b"", b"", b""]

    def _get_binary_endpoint(self) -> str:
        """Generate binary endpoint with CRC checksums and timestamp.

        Returns:
            Full endpoint path with CRC values and timestamp
            Format: binary<crc0>,<crc1>,<crc2>,<crc3> (base for auth.request)
        """
        # Correct format with commas: binary0,0,0,0
        crc_str = ",".join(self.data_crc)
        return f"binary{crc_str}.get"

    async def async_get_video_routing(self) -> dict[str, int]:
        """Get current video matrix routing.

        Returns the current input-to-output routing for video.

        Returns:
            dictionary mapping output numbers to input numbers
            Example: {1: 2, 2: 2, 3: 1, 4: 3}

        Raises:
            DeviceError: If query fails

        Example:
            >>> routing = await api.async_get_video_routing()
            >>> print(routing)  # {1: 2, 2: 2, 3: 1, 4: 3}
        """
        try:
            # Add delay to allow device to process previous command
            await asyncio.sleep(0.5)

            # Fetch with CRC values from previous query (or initial zeros)
            endpoint = self._get_binary_endpoint()
            logger.debug(f"GET request to {endpoint} with CRCs: {self.data_crc}")

            # Request binary data
            async with await self.auth.request(
                "GET",
                endpoint,
                headers={"Accept": "application/octet-stream"},
            ) as response:
                response.raise_for_status()
                content = await response.read()

            # Must have data
            if not content:
                raise ValueError("Empty response from binary endpoint")

            # Parse the binary response and update cache
            self._parse_binary_response(content)

            routing = self._parse_video_routing()
            logger.info(f"Retrieved video routing: {routing}")
            return routing

        except Exception as e:
            logger.warning(
                f"Binary status endpoint failed: {type(e).__name__}: {e}. "
                "Returning default video routing."
            )
            # Return default routing if endpoint not available
            return {str(i): 1 for i in range(1, 5)}

    def _parse_binary_response(self, data: bytes) -> None:
        """Parse binary response and update data sizes and CRCs.

        Mirrors the JavaScript ParseData function exactly.
        Data sizes are stored in LITTLE-ENDIAN format.

        Args:
            data: Binary response data from device
        """
        if len(data) < 16:
            return

        try:
            # Parse data block sizes from current header
            current_sizes = [0, 0, 0, 0]
            for i in range(4):
                offset = i * 4
                size = (
                    (data[offset + 3] << 24)
                    | (data[offset + 2] << 16)
                    | (data[offset + 1] << 8)
                    | (data[offset] & 0xFF)
                )
                current_sizes[i] = size & 0xFFFFFFFF

            # Extract data blocks and update cache
            current_offset = 16
            for i in range(4):
                if current_sizes[i] > 0:
                    block_data = data[current_offset : current_offset + current_sizes[i]]
                    current_offset += current_sizes[i]

                    crc = calculate_crc32(block_data)
                    self.data_crc[i] = crc
                    self.data_size[i] = current_sizes[i]
                    self.data_blocks[i] = block_data
                    logger.debug(f"Updated Data block {i}: size={current_sizes[i]}, crc={crc}")
                else:
                    logger.debug(f"Data block {i} unchanged (size 0)")

        except (IndexError, struct.error) as e:  # pragma: no cover
            logger.debug(f"Error parsing data block sizes: {e}")

    async def async_get_audio_output_state(self) -> dict[str, dict[str, bool]]:
        """Get current audio output state for all outputs.

        Returns the current HDMI and de-embedded audio state for each output.

        Returns:
            dictionary with output state
            Example: {
                '1': {'hdmi': True, 'de_embed': False},
                '2': {'hdmi': True, 'de_embed': False},
                '3': {'hdmi': False, 'de_embed': True},
                '4': {'hdmi': False, 'de_embed': False},
            }

        Raises:
            DeviceError: If query fails

        Example:
            >>> audio_state = await api.async_get_audio_output_state()
            >>> print(audio_state['1'])  # {'hdmi': True, 'de_embed': False}
        """
        try:
            endpoint = self._get_binary_endpoint()
            logger.debug(f"GET request to {endpoint}")

            async with await self.auth.request("GET", endpoint) as response:
                response.raise_for_status()
                content = await response.read()

            self._parse_binary_response(content)
            audio_state = self._parse_audio_state()
            logger.info(f"Retrieved audio output state: {audio_state}")
            return audio_state

        except Exception as e:
            logger.warning(
                f"Binary status endpoint not available or failed: {e}. "
                "Returning default audio state."
            )
            # Return default audio state if endpoint not available
            return {str(i): {"hdmi": True, "de_embed": False} for i in range(1, 5)}

    async def async_get_edid_configuration(self) -> dict[str, dict[str, Any]]:
        """Get current EDID configuration for all inputs.

        Returns the current EDID profile assigned to each input.

        Returns:
            dictionary with EDID configuration for each input
            Example: {
                '1': {'type': 0, 'index': 1, 'name': 'Default1'},
                '2': {'type': 0, 'index': 4, 'name': 'Default4'},
                '3': {'type': 1, 'index': 2, 'name': 'User2'},
                '4': {'type': 0, 'index': 1, 'name': 'Default1'},
            }

        Raises:
            DeviceError: If query fails

        Example:
            >>> edid_config = await api.async_get_edid_configuration()
            >>> print(edid_config['1'])  # {'type': 0, 'index': 1, 'name': 'Default1'}
        """
        try:
            endpoint = self._get_binary_endpoint()
            logger.debug(f"GET request to {endpoint}")

            async with await self.auth.request("GET", endpoint) as response:
                response.raise_for_status()
                content = await response.read()

            self._parse_binary_response(content)
            edid_config = self._parse_edid_configuration()
            logger.info(f"Retrieved EDID configuration: {edid_config}")
            return edid_config

        except Exception as e:
            logger.warning(
                f"Binary status endpoint not available or failed: {e}. "
                "Returning default EDID configuration."
            )
            # Return default EDID config if endpoint not available
            return {str(i): {"type": 0, "index": 0, "name": "Default1"} for i in range(1, 5)}

    async def async_get_port_names(self) -> dict[str, dict[str, str]]:
        """Get custom port names for inputs, outputs, and presets.

        Returns the custom names assigned to ports and presets.

        Returns:
            dictionary with port names
            Example: {
                'inputs': {
                    '1': 'Camera_Main',
                    '2': 'Camera_Backup',
                    '3': 'HDMI_1',
                    '4': 'Default',
                },
                'outputs': {
                    '1': 'Display_Main',
                    '2': 'Display_2',
                    '3': 'Display_3',
                    '4': 'Default',
                },
                'presets': {
                    '1': 'Conference',
                    '2': 'Default',
                    '3': 'Default',
                    '4': 'Default',
                    '5': 'Default',
                    '6': 'Default',
                    '7': 'Default',
                    '8': 'Default',
                }
            }

        Raises:
            DeviceError: If query fails

        Example:
            >>> names = await api.async_get_port_names()
            >>> print(names['inputs']['1'])  # 'Camera_Main'
        """
        try:
            endpoint = self._get_binary_endpoint()
            logger.debug(f"GET request to {endpoint}")

            async with await self.auth.request("GET", endpoint) as response:
                response.raise_for_status()
                content = await response.read()

            self._parse_binary_response(content)
            port_names = self._parse_port_names()
            logger.info(f"Retrieved port names: {port_names}")
            return port_names

        except Exception as e:
            logger.warning(
                f"Binary status endpoint not available or failed: {e}. "
                "Returning default port names."
            )
            # Return default port names if endpoint not available
            return {
                "inputs": {str(i): f"Input_{i}" for i in range(1, 5)},
                "outputs": {str(i): f"Output_{i}" for i in range(1, 5)},
                "presets": {str(i): f"Preset_{i}" for i in range(1, 9)},
            }

    async def async_get_full_status(self) -> dict[str, Any]:
        """Get complete device status including all routing and configuration.

        Returns all available status information from the device in one query.

        Returns:
            dictionary with complete device status

        Raises:
            DeviceError: If query fails

        Example:
            >>> status = await api.async_get_full_status()
            >>> print(status.keys())
        """
        try:
            full_status = {
                "video_routing": await self.async_get_video_routing(),
                "audio_state": await self.async_get_audio_output_state(),
                "edid_config": await self.async_get_edid_configuration(),
                "port_names": await self.async_get_port_names(),
            }

            logger.info("Retrieved complete device status")
            return full_status

        except Exception as e:
            logger.error(f"Failed to get full status: {e}")
            raise DeviceError(f"Failed to query device status: {e}") from e

    def _parse_video_routing(self) -> dict[str, int]:
        """Parse video routing from device binary response."""
        routing = {str(i): 1 for i in range(1, 5)}

        try:
            block_data = self.data_blocks[1]
            if len(block_data) < 4:  # pragma: no cover
                logger.warning("Runtime data too short, cannot parse video routing")
                return routing

            for output in range(1, 5):
                byte_idx = output - 1
                raw_val = block_data[byte_idx]
                input_val = raw_val & 0x3F

                if input_val > 4:  # pragma: no cover
                    input_val = 1

                routing[str(output)] = input_val

            logger.debug(f"Parsed video routing: {routing}")

        except (IndexError, ValueError) as e:  # pragma: no cover
            logger.debug(f"Error parsing video routing: {e}")

        return routing

    def _parse_audio_state(self) -> dict[str, dict[str, bool]]:
        """Parse binary audio output state from device response."""
        audio_state = {str(i): {"hdmi": True, "de_embed": False} for i in range(1, 5)}

        try:
            block_data = self.data_blocks[1]

            if len(block_data) < 12:  # pragma: no cover
                logger.warning("Runtime data too short for audio state")
                return audio_state

            for output in range(1, 5):
                hdmi_val = block_data[4 + (output - 1)]
                de_embed_val = block_data[8 + (output - 1)]

                audio_state[str(output)] = {
                    "hdmi": bool(hdmi_val & 0x01),
                    "de_embed": bool(de_embed_val & 0x01),
                }

            logger.debug(f"Parsed audio state: {audio_state}")

        except (IndexError, ValueError) as e:  # pragma: no cover
            logger.debug(f"Error parsing audio state: {e}")

        return audio_state

    def _parse_edid_configuration(self) -> dict[str, dict[str, Any]]:
        """Parse binary EDID configuration from device response."""
        edid_config = {str(i): {"type": 0, "index": 0, "name": "Default1"} for i in range(1, 5)}

        try:
            block_data = self.data_blocks[1]

            if len(block_data) < 20:  # pragma: no cover
                logger.warning("Runtime data too short for EDID configuration")
                return edid_config

            edid_names = [
                "Default1",
                "Default2",
                "Default3",
                "Default4",
                "Default5",
                "Default6",
                "Default7",
                "Default8",
                "User1",
                "User2",
                "User3",
                "User4",
                "Output1",
                "Output2",
                "Output3",
                "Output4",
                "Temp",
                "Reserved1",
                "Reserved2",
                "Reserved3",
                "Reserved4",
            ]

            for input_num in range(1, 5):
                edid_idx = block_data[16 + (input_num - 1)]

                if edid_idx < len(edid_names):
                    edid_name = edid_names[edid_idx]
                else:  # pragma: no cover
                    edid_name = "Unknown"
                    edid_idx = 0

                edid_config[str(input_num)] = {"type": 0, "index": edid_idx, "name": edid_name}

            logger.debug(f"Parsed EDID configuration: {edid_config}")

        except (IndexError, ValueError) as e:  # pragma: no cover
            logger.debug(f"Error parsing EDID configuration: {e}")

        return edid_config

    def _parse_port_names(self) -> dict[str, dict[str, str]]:
        """Parse binary custom port names from cached data block 3."""
        port_names = {
            "inputs": {str(i): f"Input_{i}" for i in range(1, 5)},
            "outputs": {str(i): f"Output_{i}" for i in range(1, 5)},
            "presets": {str(i): f"Preset_{i}" for i in range(1, 9)},
        }

        try:
            block_3_data = self.data_blocks[3]

            if len(block_3_data) < 256:  # pragma: no cover
                return port_names

            for i in range(4):
                name_offset = i * 16
                name_bytes = block_3_data[name_offset : name_offset + 16]
                name_str = name_bytes.split(b"\x00")[0].decode("utf-8", errors="ignore").strip()
                if name_str:
                    port_names["inputs"][str(i + 1)] = name_str

            for i in range(4):
                name_offset = (4 + i) * 16
                name_bytes = block_3_data[name_offset : name_offset + 16]
                name_str = name_bytes.split(b"\x00")[0].decode("utf-8", errors="ignore").strip()
                if name_str:
                    port_names["outputs"][str(i + 1)] = name_str

            for i in range(8):
                name_offset = 128 + (i * 16)
                name_bytes = block_3_data[name_offset : name_offset + 16]
                name_str = name_bytes.split(b"\x00")[0].decode("utf-8", errors="ignore").strip()
                if name_str:
                    port_names["presets"][str(i + 1)] = name_str

        except (IndexError, ValueError, UnicodeDecodeError) as e:  # pragma: no cover
            logger.debug(f"Error parsing port names: {e}")

        return port_names
