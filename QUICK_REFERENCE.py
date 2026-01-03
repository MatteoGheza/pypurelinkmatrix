#!/usr/bin/env python3
"""
PyPureLink Matrix Library - Complete Implementation

This file serves as a quick reference showing all implemented functionality
and how to access it through the PureLinkClient interface.
"""

# ============================================================================
# QUICK START
# ============================================================================

from pypurelinkmatrix import PureLinkClient
from pypurelinkmatrix.exceptions import AuthenticationError, PureLinkConnectionError

# Basic usage with context manager (recommended)
with PureLinkClient(host="192.168.1.100") as client:
    try:
        # Authenticate with device
        if client.login("admin", "password"):
            print("✓ Connected to PureLink device")

            # Now access any of the API modules
            # client.video  # Video matrix switching
            # client.audio  # Audio output control
            # client.edid  # EDID profile management
            # client.network  # Network configuration
            # client.system  # System management

    except AuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
    except PureLinkConnectionError as e:
        print(f"✗ Connection failed: {e}")

# ============================================================================
# COMPLETE API OVERVIEW
# ============================================================================

"""
╔════════════════════════════════════════════════════════════════════════╗
║                       VIDEO API (client.video)                        ║
╚════════════════════════════════════════════════════════════════════════╝

MATRIX SWITCHING:
  • switch_matrix(output: 0-4, input_port: 1-4)
    Route inputs to outputs. Use output=0 for all outputs.

    Examples:
      client.video.switch_matrix(1, 2)  # Input 2 → Output 1
      client.video.switch_matrix(0, 3)  # Input 3 → All outputs

PRESET MANAGEMENT:
  • save_preset(preset_num: 1-8)
    Save current matrix configuration to a preset.

    Example:
      client.video.save_preset(1)

  • recall_preset(preset_num: 1-8)
    Restore a previously saved preset.

    Example:
      client.video.recall_preset(2)

CUSTOM NAMING:
  • rename_input(input_num: 1-4, name: str)
    Set custom name for input port.

    Example:
      client.video.rename_input(1, "Presenter_Laptop")

  • rename_output(output_num: 1-4, name: str)
    Set custom name for output port.

    Example:
      client.video.rename_output(1, "MainDisplay")

  • rename_preset(preset_num: 1-8, name: str)
    Set custom name for preset.

    Example:
      client.video.rename_preset(1, "Conference_Setup")

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║                       AUDIO API (client.audio)                        ║
╚════════════════════════════════════════════════════════════════════════╝

HDMI AUDIO:
  • set_hdmi_output(output: 0-4, enabled: bool)
    Enable/disable HDMI audio on outputs.

    Examples:
      client.audio.set_hdmi_output(1, True)   # Enable on Output 1
      client.audio.set_hdmi_output(0, False)  # Disable on all

DE-EMBEDDED AUDIO:
  • set_de_embed_output(output: 0-4, enabled: bool)
    Enable/disable de-embedded audio on outputs.

    Examples:
      client.audio.set_de_embed_output(2, True)   # Enable on Output 2
      client.audio.set_de_embed_output(0, True)   # Enable on all

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║                        EDID API (client.edid)                         ║
╚════════════════════════════════════════════════════════════════════════╝

EDID PROFILES (1-17):
  Default Profiles (1-8):
    1. 4K60 444-LPCM 2.0 HDR:HLG
    2. 4K60 420-LPCM 2.0 HDR:None
    3. 4K30 444-LPCM 2.0 HDR:None
    4. 1080P60 444-LPCM 2.0 HDR:None
    5. 4K60 444-DTS 5.1 HDR:HLG
    6. 4K60 420-DTS 5.1 HDR:None
    7. 4K30 444-DTS 5.1 HDR:None
    8. 1080P60 444-DTS 5.1 HDR:None

  User Profiles (9-12): User1, User2, User3, User4
  Output Profiles (13-16): Output1, Output2, Output3, Output4
  Temp Storage (17): Temp1

INPUT EDID CONFIGURATION:
  • set_input_edid(input_num: 0-4, edid_source: 1-17)
    Set EDID profile for inputs.

    Examples:
      client.edid.set_input_edid(1, 1)   # Input 1 → Default1
      client.edid.set_input_edid(0, 4)   # All inputs → Default4

USER EDID STORAGE:
  • set_user_edid(source_profile: 1-17, destination: 0-4)
    Copy EDID to user storage slots.

    Examples:
      client.edid.set_user_edid(1, 1)   # Default1 → User1
      client.edid.set_user_edid(2, 0)   # Default2 → All user slots

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║                      NETWORK API (client.network)                     ║
╚════════════════════════════════════════════════════════════════════════╝

STATIC IP CONFIGURATION:
  • configure_static_ip(ip_address: str, subnet_mask: str, gateway: str)
    Set static IP with validation.

    Example:
      client.network.configure_static_ip(
          ip_address="192.168.1.100",
          subnet_mask="255.255.255.0",
          gateway="192.168.1.1"
      )

DHCP CONFIGURATION:
  • enable_dhcp()
    Enable automatic IP assignment.

    Example:
      client.network.enable_dhcp()

  • disable_dhcp()
    Disable DHCP for static IP mode.

    Example:
      client.network.disable_dhcp()

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║                       SYSTEM API (client.system)                      ║
╚════════════════════════════════════════════════════════════════════════╝

SYSTEM CONTROL:
  • reboot()
    Restart the device.

    Example:
      client.system.reboot()

    ⚠️  Device will disconnect during reboot

FACTORY RESET:
  • factory_reset_common()
    Reset: Video, Audio, EDID, Network
    Preserve: Presets, names, user EDID

    Example:
      client.system.factory_reset_common()

  • factory_reset_all()
    Reset everything to factory defaults.

    Example:
      client.system.factory_reset_all()

    ⚠️  Complete reset - all data will be lost

PASSWORD MANAGEMENT:
  • change_password(username: str, password: str)
    Change or create user password.

    Examples:
      client.system.change_password("admin", "newpass123")
      client.system.change_password("operator", "op_pass")

────────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════════╗
║                     DEVICE STATE (client.state)                       ║
╚════════════════════════════════════════════════════════════════════════╝

Access device state information:

  • client.state.video
    Current video matrix routing state

  • client.state.audio
    Audio output configuration state

  • client.state.edid
    EDID configuration state

  • client.state.network
    Network configuration state

  • client.state.port_names
    Custom port and preset names

  • client.state.mcu_version
    Device firmware version

────────────────────────────────────────────────────────────────────────
"""

# ============================================================================
# REALISTIC WORKFLOW EXAMPLE
# ============================================================================


def setup_conference_mode():
    """Complete device setup for video conference."""

    with PureLinkClient(host="192.168.1.100") as client:
        # Authenticate
        if not client.login("admin", "password"):
            return False

        # Configure video routing
        client.video.switch_matrix(output=1, input_port=1)  # Presenter → Main
        client.video.switch_matrix(output=2, input_port=2)  # Document cam → Secondary

        # Set custom names
        client.video.rename_input(1, "Presenter_Laptop")
        client.video.rename_input(2, "Document_Camera")
        client.video.rename_output(1, "Main_Screen")
        client.video.rename_output(2, "Secondary_Display")

        # Configure audio
        client.audio.set_hdmi_output(output=0, enabled=True)  # All outputs

        # Set EDID
        client.edid.set_input_edid(input_num=0, edid_source=1)  # 4K60 LPCM

        # Save as preset
        client.video.rename_preset(1, "Conference_Setup")
        client.video.save_preset(preset_num=1)

        return True


# ============================================================================
# ERROR HANDLING PATTERNS
# ============================================================================

"""
Always wrap operations in try-except for robust error handling:

from pypurelinkmatrix.exceptions import (
    PureLinkConnectionError,
    AuthenticationError,
    ValidationError,
    DeviceError,
)

try:
    with PureLinkClient(host="192.168.1.100") as client:
        client.login("admin", "password")
        client.video.switch_matrix(1, 2)

except ValidationError as e:
    # Invalid parameters (wrong IP, bad credentials, etc.)
    print(f"Validation error: {e}")

except AuthenticationError as e:
    # Login failed
    print(f"Authentication failed: {e}")

except PureLinkConnectionError as e:
    # Cannot reach device
    print(f"Connection failed: {e}")

except DeviceError as e:
    # Device error during operation
    print(f"Device error: {e}")
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

"""
For production use, store credentials in environment variables:

# Create .env file with:
PURELINK_HOST=192.168.1.100
PURELINK_USERNAME=admin
PURELINK_PASSWORD=secure_password

# Load in code:
import os
from dotenv import load_dotenv

load_dotenv()

client = PureLinkClient(
    host=os.getenv("PURELINK_HOST"),
    username=os.getenv("PURELINK_USERNAME"),
    password=os.getenv("PURELINK_PASSWORD"),
)
"""

# ============================================================================
# KEY FEATURES SUMMARY
# ============================================================================

"""
✓ VIDEO CONTROL
  - 4×4 matrix switching with all-outputs option
  - 8 configurable presets with custom names
  - Custom input/output/preset naming

✓ AUDIO CONTROL
  - Per-output HDMI audio enable/disable
  - Per-output de-embedded audio enable/disable
  - All-outputs control support

✓ EDID MANAGEMENT
  - 8 default EDID profiles (various resolutions/audio/HDR)
  - 4 user-defined profile slots
  - Copy from outputs and temp storage
  - Per-input profile assignment

✓ NETWORK
  - Static IP with automatic validation
  - DHCP automatic assignment
  - Gateway/subnet verification
  - Network state tracking

✓ SYSTEM
  - Device reboot
  - Factory reset (partial and complete)
  - User password management
  - Version tracking

✓ QUALITY
  - Full type hints (Python 3.9+)
  - Comprehensive error handling
  - Extensive documentation
  - Production-ready code
  - UV package management ready
"""

if __name__ == "__main__":
    print("PyPureLink Matrix Library - Implementation Complete")
    print("See README.md and API_REFERENCE.md for full documentation")
    print("Run scripts/example_full_api.py for detailed examples")
