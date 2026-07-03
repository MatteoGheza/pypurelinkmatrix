# API Reference

Complete API documentation for PyPureLink Matrix library.

## Table of Contents

- [PureLinkClient](#pureLinkClient)
- [Video API](#video-api)
- [Audio API](#audio-api)
- [EDID API](#edid-api)
- [Network API](#network-api)
- [System API](#system-api)
- [Data Models](#data-models)
- [Exceptions](#exceptions)

---

## PureLinkClient

Main client class for connecting to PureLink matrix devices.

### Constructor

```python
PureLinkClient(
    session: aiohttp.ClientSession,
    host: str,
    username: str = "",
    password: str = "",
    timeout: int = 30,
    use_https: bool = False,
    verify_ssl: bool = True
)
```

**Parameters:**
- `session` - `aiohttp.ClientSession` instance (required)
- `host` - Device IP address or hostname (required)
- `username` - Login username (1-15 alphanumeric/underscore)
- `password` - Login password (1-15 alphanumeric/underscore)
- `timeout` - Request timeout in seconds (default: 30)
- `use_https` - Use HTTPS for connection (default: False)
- `verify_ssl` - Verify SSL certificates (default: True)

### Methods

#### async_login(username=None, password=None) -> bool

Authenticate with the device.

```python
async with aiohttp.ClientSession() as session:
    client = PureLinkClient(session, host="192.168.1.100")
    if await client.async_login("admin", "password"):
        print("Authenticated!")
```

#### close()

Close the client session and cleanup resources.

```python
client.close()
```

### Context Manager

Use `with` statement for automatic cleanup:

```python
with PureLinkClient(host="192.168.1.100") as client:
    client.login("admin", "password")
    # Use client here
    # Automatically closes on exit
```

### Nested APIs

Access API modules through client instance:

```python
client.video     # Video matrix control
client.audio     # Audio output control
client.edid      # EDID configuration
client.network   # Network settings
client.system    # System management
```

---

## Video API

Video matrix switching and preset management.

Access via: `client.video`

### Methods

#### async_switch_matrix(output: int, input_port: int, timeout: int = 30) -> bool

Route an input to an output(s).

```python
# Route Input 2 to Output 1
await client.video.async_switch_matrix(output_port=1, input_port=2)

# Route Input 3 to all outputs
await client.video.async_switch_matrix(output_port=0, input_port=3)
```

**Parameters:**
- `output` - 0 = all outputs, 1-4 = specific output
- `input_port` - 1-4 = input port number
- `timeout` - Request timeout in seconds

---

#### async_save_preset(preset_num: int, timeout: int = 30) -> bool

Save current configuration to a preset.

```python
# Save to Preset 1
await client.video.async_save_preset(preset_num=1)
```

**Parameters:**
- `preset_num` - 1-8 = preset number
- `timeout` - Request timeout in seconds

---

#### async_recall_preset(preset_num: int, timeout: int = 30) -> bool

Restore a previously saved preset.

```python
# Load Preset 2
await client.video.async_recall_preset(preset_num=2)
```

**Parameters:**
- `preset_num` - 1-8 = preset number
- `timeout` - Request timeout in seconds

---

#### async_rename_input(input_num: int, name: str, timeout: int = 30) -> bool

Set custom name for an input port.

```python
await client.video.async_rename_input(1, "Camera_Main")
await client.video.async_rename_input(2, "Laptop_Presenter")
```

**Parameters:**
- `input_num` - 1-4 = input number
- `name` - Custom name (1-15 alphanumeric/underscore)
- `timeout` - Request timeout in seconds

---

#### async_rename_output(output_num: int, name: str, timeout: int = 30) -> bool

Set custom name for an output port.

```python
await client.video.async_rename_output(1, "MainDisplay")
await client.video.async_rename_output(2, "SecondDisplay")
```

**Parameters:**
- `output_num` - 1-4 = output number
- `name` - Custom name (1-15 alphanumeric/underscore)
- `timeout` - Request timeout in seconds

---

#### async_rename_preset(preset_num: int, name: str, timeout: int = 30) -> bool

Set custom name for a preset.

```python
await client.video.async_rename_preset(1, "Conference")
await client.video.async_rename_preset(2, "Presentation")
```

**Parameters:**
- `preset_num` - 1-8 = preset number
- `name` - Custom name (1-15 alphanumeric/underscore)
- `timeout` - Request timeout in seconds

---

## Audio API

Audio output configuration.

Access via: `client.audio`

### Methods

#### async_set_hdmi_output(output: int, enabled: bool, timeout: int = 30) -> bool

Enable/disable HDMI audio output.

```python
# Enable HDMI on Output 1
await client.audio.async_set_hdmi_output(output=1, enabled=True)

# Disable HDMI on all outputs
await client.audio.async_set_hdmi_output(output=0, enabled=False)
```

**Parameters:**
- `output` - 0 = all outputs, 1-4 = specific output
- `enabled` - True = enable, False = disable
- `timeout` - Request timeout in seconds

---

#### async_set_de_embed_output(output: int, enabled: bool, timeout: int = 30) -> bool

Enable/disable de-embedded audio output.

```python
# Enable de-embed on Output 2
await client.audio.async_set_de_embed_output(output=2, enabled=True)

# Enable on all outputs
await client.audio.async_set_de_embed_output(output=0, enabled=True)
```

**Parameters:**
- `output` - 0 = all outputs, 1-4 = specific output
- `enabled` - True = enable, False = disable
- `timeout` - Request timeout in seconds

---

## EDID API

EDID profile configuration and management.

Access via: `client.edid`

### EDID Profiles

Available EDID sources (1-17):

**Default Profiles (1-8):**
1. Default1: 4K60 444-LPCM 2.0, HDR:HLG
2. Default2: 4K60 420-LPCM 2.0, HDR:None
3. Default3: 4K30 444-LPCM 2.0, HDR:None
4. Default4: 1080P60 444-LPCM 2.0, HDR:None
5. Default5: 4K60 444-DTS 5.1, HDR:HLG
6. Default6: 4K60 420-DTS 5.1, HDR:None
7. Default7: 4K30 444-DTS 5.1, HDR:None
8. Default8: 1080P60 444-DTS 5.1, HDR:None

**User Profiles (9-12):**
- 9: User1 (custom)
- 10: User2 (custom)
- 11: User3 (custom)
- 12: User4 (custom)

**Output Profiles (13-16):**
- 13: Output1 EDID
- 14: Output2 EDID
- 15: Output3 EDID
- 16: Output4 EDID

**Temp (17):**
- 17: Temp1 (temporary storage)

### Methods

#### async_set_input_edid(input_num: int, edid_source: int, timeout: int = 30) -> bool

Configure EDID for an input.

```python
# Set 4K60 LPCM on Input 1
await client.edid.async_set_input_edid(input_num=1, edid_source=1)

# Set 1080P60 on Input 2
await client.edid.async_set_input_edid(input_num=2, edid_source=4)

# Set same EDID on all inputs
await client.edid.async_set_input_edid(input_num=0, edid_source=3)
```

**Parameters:**
- `input_num` - 0 = all inputs, 1-4 = specific input
- `edid_source` - 1-17 = EDID profile number
- `timeout` - Request timeout in seconds

---

#### async_set_user_edid(source_profile: int, destination: int, timeout: int = 30) -> bool

Copy EDID profile to user storage.

```python
# Copy Default1 to User1
await client.edid.async_set_user_edid(source_profile=1, destination=1)

# Copy Default4 to all user slots
await client.edid.async_set_user_edid(source_profile=4, destination=0)

# Copy Output1 EDID to User2
await client.edid.async_set_user_edid(source_profile=13, destination=2)
```

**Parameters:**
- `source_profile` - 1-17 = source EDID profile
- `destination` - 0 = all user slots, 1-4 = specific user slot
- `timeout` - Request timeout in seconds

---

## Network API

Network configuration.

Access via: `client.network`

### Methods

#### async_configure_static_ip(ip_address: str, subnet_mask: str, gateway: str, timeout: int = 30) -> bool

Configure static IP address.

```python
await client.network.async_configure_static_ip(
    ip_address="192.168.1.100",
    subnet_mask="255.255.255.0",
    gateway="192.168.1.1"
)
```

**Parameters:**
- `ip_address` - IP address (xxx.xxx.xxx.xxx)
- `subnet_mask` - Subnet mask (xxx.xxx.xxx.xxx)
- `gateway` - Default gateway (xxx.xxx.xxx.xxx)
- `timeout` - Request timeout in seconds

**Validation:**
- All three must be valid IP addresses
- Gateway must be on the same subnet as IP address

---

#### async_enable_dhcp(timeout: int = 30) -> bool

Enable DHCP for automatic IP configuration.

```python
await client.network.async_enable_dhcp()
```

**Parameters:**
- `timeout` - Request timeout in seconds

---

#### async_disable_dhcp(timeout: int = 30) -> bool

Disable DHCP for static IP mode.

```python
await client.network.async_disable_dhcp()
```

**Parameters:**
- `timeout` - Request timeout in seconds

---

## System API

System management and configuration.

Access via: `client.system`

### Methods

#### async_reboot(timeout: int = 30) -> bool

Reboot the device.

```python
await client.system.async_reboot()
```

**Parameters:**
- `timeout` - Request timeout in seconds

⚠️ **Warning:** Device will disconnect during reboot.

---

#### async_factory_reset_common(timeout: int = 30) -> bool

Reset common settings to factory defaults.

Resets: Video, Audio, EDID, Network settings
Preserves: Presets, custom names, user EDID profiles

```python
await client.system.async_factory_reset_common()
```

**Parameters:**
- `timeout` - Request timeout in seconds

⚠️ **Warning:** Device will restart after reset.

---

#### async_factory_reset_all(timeout: int = 30) -> bool

Reset all settings to factory defaults.

Resets: Everything including presets and user data

```python
await client.system.async_factory_reset_all()
```

**Parameters:**
- `timeout` - Request timeout in seconds

⚠️ **Warning:** This is a complete reset. All custom configuration will be lost.

---

#### async_change_password(username: str, password: str, timeout: int = 30) -> bool

Change or create user password.

```python
# Change admin password
await client.system.async_change_password("admin", "newpass123")

# Create new user
await client.system.async_change_password("operator", "operator_pass")
```

**Parameters:**
- `username` - Username (1-15 alphanumeric/underscore)
- `password` - New password (1-15 alphanumeric/underscore)
- `timeout` - Request timeout in seconds

---

## Data Models

### DeviceState

Complete device state container.

```python
state = client.state

# Access state components
state.video      # VideoMatrixState
state.audio      # AudioState
state.edid       # EDIDState
state.network    # NetworkState
state.port_names # PortNames
```

### VideoMatrixState

Video matrix routing configuration (read-only, updated automatically by API calls).

```python
# Get current routing
input_port = state.video.get_output_input(output=1)

# Use API to set routing (updates state automatically)
await client.video.async_switch_matrix(output_port=1, input_port=2)
```

### AudioState

Audio output configuration for all outputs (read-only, updated automatically by API calls).

```python
output_1 = state.audio.get_output(1)
if output_1:
    print(output_1.hdmi_enabled)
    print(output_1.de_embed_enabled)

# Use API to change settings (updates state automatically)
await client.audio.async_set_hdmi_output(output=1, enabled=True)
```

### EDIDState

EDID configuration for all inputs (read-only, updated automatically by API calls).

```python
# Get current EDID
edid = state.edid.get_input_edid(input_num=1)

# Use API to set EDID (updates state automatically)
await client.edid.async_set_input_edid(input_num=1, edid_source=1)
```

### NetworkState

Network configuration.

```python
print(state.network.ip_address)
print(state.network.subnet_mask)
print(state.network.gateway)
print(state.network.mac_address)
```

### PortNames

Custom port and preset names.

```python
state.port_names.set_input_name(1, "Camera_Main")
state.port_names.set_output_name(1, "MainDisplay")
state.port_names.set_preset_name(1, "Conference")
```

---

## Exceptions

### Exception Hierarchy

```
PureLinkError (base)
├── PureLinkConnectionError
├── AuthenticationError
├── ValidationError
└── DeviceError
```

### Exception Usage

```python
from pypurelinkmatrix.exceptions import (
    PureLinkConnectionError,
    AuthenticationError,
    ValidationError,
    DeviceError,
)

async with aiohttp.ClientSession() as session:
    try:
        client = PureLinkClient(session, host="192.168.1.100")
        await client.async_login("admin", "password")
    except ValidationError as e:
        print(f"Invalid input: {e}")
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except PureLinkConnectionError as e:
        print(f"Cannot connect to device: {e}")
    except DeviceError as e:
        print(f"Device error: {e}")
```

---

## Common Workflows

### Complete Device Setup

```python
async with aiohttp.ClientSession() as session:
    client = PureLinkClient(session, host="192.168.1.100")

    # Authenticate
    await client.async_login("admin", "password")

    # Configure video routing
    await client.video.async_switch_matrix(output_port=1, input_port=1)
    await client.video.async_switch_matrix(output_port=2, input_port=2)

    # Set names
    await client.video.async_rename_input(1, "Presenter")
    await client.video.async_rename_output(1, "Main_Screen")

    # Configure audio
    await client.audio.async_set_hdmi_output(output=0, enabled=True)

    # Set EDID
    await client.edid.async_set_input_edid(input_num=0, edid_source=1)

    # Save preset
    await client.video.async_save_preset(preset_num=1)
```

### Preset Management

```python
# Create preset
await client.video.async_switch_matrix(1, 1)
await client.video.async_switch_matrix(2, 2)
await client.video.async_rename_preset(1, "Conference")
await client.video.async_save_preset(1)

# Later: Recall preset
await client.video.async_recall_preset(1)
```

### Network Configuration

```python
# Configure static IP
await client.network.async_configure_static_ip(
    ip_address="192.168.1.100",
    subnet_mask="255.255.255.0",
    gateway="192.168.1.1"
)

# Or enable DHCP
await client.network.async_enable_dhcp()
```

---

## Error Handling

Always wrap operations in try-except blocks:

```python
try:
    await client.video.async_switch_matrix(output_port=1, input_port=2)
except ValueError as e:
    print(f"Invalid parameters: {e}")
except DeviceError as e:
    print(f"Device error: {e}")
```

---

## Logging

Enable debug logging to see API commands:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Now API calls will be logged
await client.video.async_switch_matrix(1, 2)
```

For more examples, see `examples/example_full_api.py`
