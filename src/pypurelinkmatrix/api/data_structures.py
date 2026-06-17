"""Data structures for device status following the JavaScript pattern.

This module mirrors the JS data structures from the original implementation:
- IP_INFO_T: Network configuration data
- RUN_INF_T: Device runtime state
- STRING_INF_T: String data (names)
- Web_Info: Complete device information container
"""

from dataclasses import dataclass, field


@dataclass
class IPInfo:
    """Network configuration data (IP_INFO_T equivalent).

    Mirrors the JS structure:
    function IP_INFO_T() {
        this.dhcp=0;
        this.ip=0;
        this.mask=0;
        this.gw=0;
        this.dns=0;
        this.mac=0;
        this.port=0;
        this.device_id=0;
        this.netbios=0;
    }
    """

    dhcp: int = 0
    ip: str = "0.0.0.0"
    mask: str = "0.0.0.0"
    gw: str = "0.0.0.0"
    dns: str = "0.0.0.0"
    mac: str = "00:00:00:00:00:00"
    port: int = 0
    device_id: str = ""
    netbios: str = ""


@dataclass
class RunInfo:
    """Device runtime state (RUN_INF_T equivalent).

    Mirrors the JS structure containing all runtime state data.
    """

    # Video matrix state: which input is connected to each output
    video_mx: list[int] = field(default_factory=lambda: [0] * 4)

    # Video on/off state for each output
    video_nf: list[int] = field(default_factory=lambda: [0] * 4)

    # Audio HDMI state for each output
    audio_hdmi: list[int] = field(default_factory=lambda: [0] * 4)

    # Audio de-embedded state for each output
    audio_dec: list[int] = field(default_factory=lambda: [0] * 4)

    # EDID modification flags
    edid_mdf: list[int] = field(default_factory=lambda: [0] * 4)

    # EDID configuration data
    edid_cfg: list[int] = field(default_factory=lambda: [0] * (4 * (4 + 16 + 1)))

    # Active EDID index for each input
    edid_inf: list[int] = field(default_factory=lambda: [0] * 4)

    # Input port status (connection status)
    in_port_status: list[int] = field(default_factory=lambda: [0] * 4)

    # Output port status (connection status)
    out_port_status: list[int] = field(default_factory=lambda: [0] * 4)


@dataclass
class StringInfo:
    """String data for naming and labels (STRING_INF_T equivalent).

    Mirrors the JS structure containing all string/label data.
    """

    # EDID information/descriptions (21 EDID profiles)
    edid_info: list[str] = field(default_factory=lambda: [""] * 21)

    # Port names (8 total: 4 inputs + 4 outputs)
    port_name: list[str] = field(default_factory=lambda: [""] * 8)

    # Preset names (8 presets)
    preset_name: list[str] = field(default_factory=lambda: [""] * 8)


@dataclass
class WebInfo:
    """Complete device information (Web_Info equivalent).

    Container for all device data following the JS pattern:
    function Web_Info() {
        this.ip=new IP_INFO_T();
        this.run=new RUN_INF_T();
        this.name=new STRING_INF_T();
    }
    """

    ip: IPInfo = field(default_factory=IPInfo)
    run: RunInfo = field(default_factory=RunInfo)
    name: StringInfo = field(default_factory=StringInfo)

    def reset(self) -> None:
        """Reset all data to default values."""
        self.ip = IPInfo()
        self.run = RunInfo()
        self.name = StringInfo()
