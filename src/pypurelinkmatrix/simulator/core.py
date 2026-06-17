"""Core logic for PureLink Matrix Simulator."""

import logging
import struct
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_crc32(data: bytes) -> int:
    """Calculate CRC32 using the device's specific algorithm.

    Polynomial: 0x04C11DB7
    Init: 0xFFFFFFFF
    """
    crc = 0xFFFFFFFF
    polynomial = 0x04C11DB7

    # Convert bytes to 32-bit uints (little-endian)
    words = []
    for i in range(0, len(data), 4):
        word = 0
        for j in range(min(4, len(data) - i)):
            word |= data[i + j] << (j * 8)
        # Pad with 0xFF if not a full word
        if len(data) - i < 4:
            for j in range(len(data) - i, 4):
                word |= 0xFF << (j * 8)
        words.append(word & 0xFFFFFFFF)

    for dat in words:
        mask = 0x80000000
        while mask:
            if crc & 0x80000000:
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1

            if dat & mask:
                crc = crc ^ polynomial

            mask >>= 1
            crc &= 0xFFFFFFFF

    return crc


class MatrixSimulator:
    """Simulates the state and behavior of a PureLink PT-MA-HD44M Matrix."""

    def __init__(self) -> None:
        # Network State (Block 0)
        self.dhcp: int = 0  # 0=ON, 1=OFF
        self.ip: str = "192.168.1.168"
        self.mask: str = "255.255.255.0"
        self.gw: str = "192.168.1.1"
        self.dns: str = "8.8.8.8"
        self.mac: str = "00:11:22:33:44:55"

        # Runtime State (Block 1)
        self.video_mx: list[int] = [1, 1, 1, 1]  # Output -> Input (1-based)
        self.video_nf: list[int] = [1, 1, 1, 1]  # 1=ON, 0=OFF
        self.audio_hdmi: list[int] = [1, 1, 1, 1]  # 1=ON, 0=OFF
        self.audio_dec: list[int] = [0, 0, 0, 0]  # 1=ON, 0=OFF
        self.edid_mdf: list[int] = [0, 0, 0, 0]
        self.edid_cfg: list[int] = [0] * (4 * 21)
        # Initialize EDID info: Input 1-4 all use Default 1
        for i in range(4):
            self.edid_cfg[21 * i] = 1

        self.in_port_status: list[int] = [1, 1, 1, 1]
        self.out_port_status: list[int] = [1, 1, 1, 1]

        # EDID Strings (Block 2)
        self.edid_info: list[str] = ["" for _ in range(21)]
        self._init_edid_strings()

        # Names (Block 3)
        self.port_names: list[str] = [f"Input{i+1}" for i in range(4)] + [
            f"Output{i+1}" for i in range(4)
        ]
        self.preset_names: list[str] = [f"Preset {i+1}" for i in range(8)]

        # Presets (Saved routing)
        self.presets: dict[int, list[int]] = {i: [1, 1, 1, 1] for i in range(1, 9)}

        # System
        self.username = "admin"
        self.password = "admin"
        self.mcu_version = "V1.0.0"

    def _init_edid_strings(self):
        defaults = [
            "Default1:4K60 444-LPCM: 2.0, HDR:HLG",
            "Default2:4K60 420-LPCM: 2.0, HDR:None",
            "Default3:4K30 444-LPCM: 2.0, HDR:None",
            "Default4:1080P60 444-LPCM: 2.0, HDR:None",
            "Default5:4K60 444-DTS: 5.1, HDR:HLG",
            "Default6:4K60 420-DTS: 5.1, HDR:None",
            "Default7:4K30 444-DTS: 5.1, HDR:None",
            "Default8:1080P60 444-DTS: 5.1, HDR:None",
        ]
        for i, d in enumerate(defaults):
            self.edid_info[i] = d
        for i in range(8, 12):
            self.edid_info[i] = f"User{i-7}"
        for i in range(12, 16):
            self.edid_info[i] = f"Output{i-11}"
        self.edid_info[16] = "Temp1"

    def process_command(self, cmd: str) -> str:
        """Process a device command string."""
        logger.debug(f"Simulator processing command: {cmd}")

        # Support multi-commands
        parts = cmd.split("#")
        results = []
        for part in parts:
            if not part:
                continue
            res = self._handle_single_command("#" + part)
            if res:
                results.append(res)

        return "".join(results) if results else "OK"

    def reset(self) -> None:
        """Reset the simulator state."""
        self.dhcp = 0  # 0=ON, 1=OFF
        self.ip = "192.168.1.168"
        self.mask = "255.255.255.0"
        self.gw = "192.168.1.1"
        self.dns = "8.8.8.8"
        self.mac = "00:11:22:33:44:55"

        self.video_mx = [1, 1, 1, 1]  # Output -> Input (1-based)
        self.video_nf = [1, 1, 1, 1]  # 1=ON, 0=OFF
        self.audio_hdmi = [1, 1, 1, 1]  # 1=ON, 0=OFF
        self.audio_dec = [0, 0, 0, 0]  # 1=ON, 0=OFF
        self.edid_mdf = [0, 0, 0, 0]
        self.edid_cfg = [0] * (4 * 21)
        for i in range(4):
            self.edid_cfg[21 * i] = 1

        self.in_port_status = [1, 1, 1, 1]
        self.out_port_status = [1, 1, 1, 1]

        self.edid_info = ["" for _ in range(21)]
        self._init_edid_strings()

        self.port_names = [f"Input{i+1}" for i in range(4)] + [f"Output{i+1}" for i in range(4)]
        self.preset_names = [f"Preset {i+1}" for i in range(8)]

        self.presets = {i: [1, 1, 1, 1] for i in range(1, 9)}

        self.username = "admin"
        self.password = "admin"
        self.mcu_version = "V1.0.0"

    def _handle_single_command(self, cmd: str) -> Optional[str]:
        # Video Routing: #video_d out256 matrix=1
        if cmd.startswith("#video_d"):
            import re

            match = re.search(r"out(\d+) matrix=(\d+)", cmd)
            if match:
                out_port = int(match.group(1))
                in_port = int(match.group(2))
                if out_port == 256:  # All
                    for i in range(4):
                        self.video_mx[i] = in_port
                elif 1 <= out_port <= 4:
                    self.video_mx[out_port - 1] = in_port
            return None

        # Audio Output: #audio_d out1 hdmi=1
        if cmd.startswith("#audio_d"):
            import re

            match = re.search(r"out(\d+) (hdmi|dec)=(\d)", cmd)
            if match:
                out_port = int(match.group(1))
                mode = match.group(2)
                val = int(match.group(3))
                ports = range(1, 5) if out_port == 0 else [out_port]
                for p in ports:
                    if 1 <= p <= 4:
                        if mode == "hdmi":
                            self.audio_hdmi[p - 1] = val
                        else:
                            self.audio_dec[p - 1] = val
            return None

        # Presets: #preset:1 exe=1 (Save) or exe=0 (Recall)
        if cmd.startswith("#preset"):
            import re

            match = re.search(r"preset:(\d+) exe=(\d)", cmd)
            if match:
                num = int(match.group(1))
                exe = int(match.group(2))
                if 1 <= num <= 8:
                    if exe == 1:  # Save
                        self.presets[num] = list(self.video_mx)
                    else:  # Recall
                        self.video_mx = list(self.presets[num])
            return None

        # EDID: #edid in1 cfg=0/1
        if cmd.startswith("#edid"):
            import re

            # Handle #edid inX cfg=T/I
            match = re.search(r"in(\d+) cfg=(\d)/(\d+)", cmd)
            if match:
                in_port = int(match.group(1))
                e_type = int(match.group(2))
                e_idx = int(match.group(3))

                # Calculate absolute index in edid_info
                abs_idx = 0
                if e_type == 0:
                    abs_idx = e_idx - 1
                elif e_type == 1:
                    abs_idx = 8 + e_idx - 1
                elif e_type == 2:
                    abs_idx = 12 + e_idx - 1
                elif e_type == 4:
                    abs_idx = 16

                ports = range(1, 5) if in_port == 0 else [in_port]
                for p in ports:
                    if 1 <= p <= 4:
                        # Reset all flags for this input
                        for i in range(21):
                            self.edid_cfg[21 * (p - 1) + i] = 0
                        # Set active flag
                        if 0 <= abs_idx < 21:
                            self.edid_cfg[21 * (p - 1) + abs_idx] = 1

            # Handle #edid userX cfg=T/I (Copy to User EDID)
            match = re.search(r"user(\d+) cfg=(\d)/(\d+)", cmd)
            if match:
                dest_user = int(match.group(1))  # 1-4, 0=All
                e_type = int(match.group(2))
                e_idx = int(match.group(3))

                # Find source EDID string
                src_abs_idx = 0
                if e_type == 0:
                    src_abs_idx = e_idx - 1
                elif e_type == 1:
                    src_abs_idx = 8 + e_idx - 1
                elif e_type == 2:
                    src_abs_idx = 12 + e_idx - 1
                elif e_type == 4:
                    src_abs_idx = 16

                if 0 <= src_abs_idx < 21:
                    src_str = self.edid_info[src_abs_idx]
                    users = range(1, 5) if dest_user == 0 else [dest_user]
                    for u in users:
                        self.edid_info[8 + u - 1] = src_str
            return None

        # Names: #name0 str=Input1
        if cmd.startswith("#name"):
            import re

            match = re.search(r"name(\d+) str=(.*)", cmd)
            if match:
                idx: int = int(match.group(1))
                name_val: str = match.group(2)
                if 0 <= idx <= 7:
                    self.port_names[idx] = name_val
                elif 8 <= idx <= 15:
                    self.preset_names[idx - 8] = name_val
            return None

        # IP: #ip dhcp=0
        if cmd.startswith("#ip"):
            import re

            match = re.search(r"dhcp=(\d)", cmd)
            if match:
                self.dhcp = int(match.group(1))

            match = re.search(r"ip=([\d\.]+) mask=([\d\.]+) gw=([\d\.]+)", cmd)
            if match:
                self.ip = match.group(1)
                self.mask = match.group(2)
                self.gw = match.group(3)
            return None

        # System: #factory0, #factory1, #power start=1
        if cmd == "#factory0":
            # Common reset (keep names/presets)
            self.video_mx = [1, 1, 1, 1]
            self.audio_hdmi = [1, 1, 1, 1]
            self.audio_dec = [0, 0, 0, 0]
            return None
        if cmd == "#factory1":
            # All reset
            self.reset()
            return None
        # Login/Register
        if cmd.startswith("#login"):
            # Return status:1 for success
            return '{"status":1}'
        if cmd.startswith("#register255"):
            import re

            match = re.search(r"id=(.*) psd=(.*)", cmd)
            if match:
                self.username = match.group(1)
                self.password = match.group(2)
            return '{"status":1}'

        return None

    def get_binary_data(self) -> bytes:
        """Generate the full binary status response."""
        # Block 0: Network (23 bytes)
        block0 = bytearray([self.dhcp])
        for part in self.ip.split("."):
            block0.append(int(part))
        for part in self.mask.split("."):
            block0.append(int(part))
        for part in self.gw.split("."):
            block0.append(int(part))
        for part in self.dns.split("."):
            block0.append(int(part))
        for part in self.mac.split(":"):
            block0.append(int(part, 16))

        # Block 1: Runtime
        block1 = bytearray()
        # video_mx (4 bytes)
        for val in self.video_mx:
            block1.append(val & 0x3F)
        # video_nf (4 bytes)
        for val in self.video_nf:
            block1.append(val & 0x3F)
        # audio_hdmi (4 bytes)
        for val in self.audio_hdmi:
            block1.append(val & 0x3F)
        # audio_dec (4 bytes)
        for val in self.audio_dec:
            block1.append(val & 0x3F)
        # edid_mdf (16 bytes)
        for val in self.edid_mdf:
            block1.extend(struct.pack("<I", val))
        # edid_cfg (84 bytes)
        for val in self.edid_cfg:
            block1.append(val & 0x3F)

        # Calculate exactly how many bytes are needed to reach the end of the block
        # The parser expects port status in the last 36 bytes of Block 1.
        # Total size of Block 1 in device is usually fixed or calculated.
        # Let's use a fixed size for Block 1 that matches the parser's expectation.

        # Header + audio/video/edid = 4 + 4 + 4 + 4 + 16 + 84 = 116 bytes.
        # Port status = 36 bytes.
        # Total = 152 bytes.

        current_len = len(block1)
        target_len = 152
        if current_len < target_len - 36:
            block1.extend(b"\x00" * (target_len - 36 - current_len))

        # Port Status (last 36 bytes)
        # In port status: 4 ports * 8 bytes
        for i in range(4):
            block1.append(self.in_port_status[i] & 0x01)
            block1.extend(b"\x00" * 7)
        # Out port status: 4 ports * 1 byte
        for i in range(4):
            block1.append(self.out_port_status[i] & 0x01)

        # Block 2: EDID Strings (21 * 64 = 1344 bytes)
        block2 = bytearray()
        for s in self.edid_info:
            s_bytes = s.encode("utf-8")[:63]
            block2.extend(s_bytes)
            block2.extend(b"\x00" * (64 - len(s_bytes)))

        # Block 3: Names (16 * 16 = 256 bytes)
        block3 = bytearray()
        # 8 port names (4 in, 4 out)
        for n in self.port_names:
            n_bytes = n.encode("utf-8")[:15]
            block3.extend(n_bytes)
            block3.extend(b"\x00" * (16 - len(n_bytes)))
        # 8 preset names
        for n in self.preset_names:
            n_bytes = n.encode("utf-8")[:15]
            block3.extend(n_bytes)
            block3.extend(b"\x00" * (16 - len(n_bytes)))

        # Header: 4 uint32 sizes
        header = struct.pack("<IIII", len(block0), len(block1), len(block2), len(block3))

        return header + block0 + block1 + block2 + block3
