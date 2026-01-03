"""Device state and data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VideoMatrixMode(Enum):
    """Video matrix output modes."""

    OUTPUT_1 = 1
    OUTPUT_2 = 2
    OUTPUT_3 = 3
    OUTPUT_4 = 4
    OUTPUT_ALL = 0


class InputPort(Enum):
    """Available input ports."""

    INPUT_1 = 1
    INPUT_2 = 2
    INPUT_3 = 3
    INPUT_4 = 4


class PresetMode(Enum):
    """Preset operation modes."""

    SAVE = 1
    RECALL = 0


class EDIDType(Enum):
    """EDID profile types."""

    DEFAULT_1 = "Default1:4K60 444-LPCM: 2.0, HDR:HLG"
    DEFAULT_2 = "Default2:4K60 420-LPCM: 2.0, HDR:None"
    DEFAULT_3 = "Default3:4K30 444-LPCM: 2.0, HDR:None"
    DEFAULT_4 = "Default4:1080P60 444-LPCM: 2.0, HDR:None"
    DEFAULT_5 = "Default5:4K60 444-DTS: 5.1, HDR:HLG"
    DEFAULT_6 = "Default6:4K60 420-DTS: 5.1, HDR:None"
    DEFAULT_7 = "Default7:4K30 444-DTS: 5.1, HDR:None"
    DEFAULT_8 = "Default8:1080P60 444-DTS: 5.1, HDR:None"


@dataclass
class VideoMatrixState:
    """Current video matrix state."""

    output_1_input: int = 0
    output_2_input: int = 0
    output_3_input: int = 0
    output_4_input: int = 0

    def set_output_input(self, output: int, input_port: int) -> None:
        """Set which input is routed to an output."""
        if output == 1:
            self.output_1_input = input_port
        elif output == 2:
            self.output_2_input = input_port
        elif output == 3:
            self.output_3_input = input_port
        elif output == 4:
            self.output_4_input = input_port

    def get_output_input(self, output: int) -> int:
        """Get which input is routed to an output."""
        if output == 1:
            return self.output_1_input
        elif output == 2:
            return self.output_2_input
        elif output == 3:
            return self.output_3_input
        elif output == 4:
            return self.output_4_input
        return 0


@dataclass
class AudioOutputState:
    """Audio output state for a single output."""

    output_num: int
    hdmi_enabled: bool = False
    de_embed_enabled: bool = False


@dataclass
class AudioState:
    """Current audio output state."""

    output_1: AudioOutputState = field(default_factory=lambda: AudioOutputState(1))
    output_2: AudioOutputState = field(default_factory=lambda: AudioOutputState(2))
    output_3: AudioOutputState = field(default_factory=lambda: AudioOutputState(3))
    output_4: AudioOutputState = field(default_factory=lambda: AudioOutputState(4))

    def get_output(self, output_num: int) -> Optional[AudioOutputState]:
        """Get audio state for a specific output."""
        if output_num == 1:
            return self.output_1
        elif output_num == 2:
            return self.output_2
        elif output_num == 3:
            return self.output_3
        elif output_num == 4:
            return self.output_4
        return None


@dataclass
class EDIDState:
    """EDID configuration state."""

    input_1_edid: int = 0
    input_2_edid: int = 0
    input_3_edid: int = 0
    input_4_edid: int = 0

    def set_input_edid(self, input_num: int, edid_index: int) -> None:
        """Set EDID for an input."""
        if input_num == 1:
            self.input_1_edid = edid_index
        elif input_num == 2:
            self.input_2_edid = edid_index
        elif input_num == 3:
            self.input_3_edid = edid_index
        elif input_num == 4:
            self.input_4_edid = edid_index

    def get_input_edid(self, input_num: int) -> int:
        """Get EDID for an input."""
        if input_num == 1:
            return self.input_1_edid
        elif input_num == 2:
            return self.input_2_edid
        elif input_num == 3:
            return self.input_3_edid
        elif input_num == 4:
            return self.input_4_edid
        return 0


@dataclass
class NetworkState:
    """Network configuration state."""

    dhcp_enabled: bool = False
    ip_address: str = "192.168.1.100"
    subnet_mask: str = "255.255.255.0"
    gateway: str = "192.168.1.1"
    dns: str = "8.8.8.8"
    mac_address: str = "00:00:00:00:00:00"
    device_port: int = 0
    device_id: str = ""


@dataclass
class PortNames:
    """Port naming configuration."""

    input_names: list[str] = field(default_factory=lambda: [f"Input{i+1}" for i in range(4)])
    output_names: list[str] = field(default_factory=lambda: [f"Output{i+1}" for i in range(4)])
    preset_names: list[str] = field(default_factory=lambda: [f"Preset {i+1}" for i in range(8)])

    def set_input_name(self, input_num: int, name: str) -> None:
        """Set name for an input port."""
        if 1 <= input_num <= 4:
            self.input_names[input_num - 1] = name

    def set_output_name(self, output_num: int, name: str) -> None:
        """Set name for an output port."""
        if 1 <= output_num <= 4:
            self.output_names[output_num - 1] = name

    def set_preset_name(self, preset_num: int, name: str) -> None:
        """Set name for a preset."""
        if 1 <= preset_num <= 8:
            self.preset_names[preset_num - 1] = name


@dataclass
class DeviceState:
    """Complete device state."""

    video: VideoMatrixState = field(default_factory=VideoMatrixState)
    audio: AudioState = field(default_factory=AudioState)
    edid: EDIDState = field(default_factory=EDIDState)
    network: NetworkState = field(default_factory=NetworkState)
    port_names: PortNames = field(default_factory=PortNames)
    mcu_version: str = "Unknown"
