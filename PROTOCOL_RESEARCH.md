# PureLink PT-MA-HD44M Protocol Documentation

This document outlines the reverse-engineered protocol for the PureLink PT-MA-HD44M matrix switcher, based on analysis of the official web interface and captured network traffic.

## 1. Connection & Authentication

### HTTP Connection
- The device runs a basic HTTP server (usually on port 80).
- **Authentication**: Uses a custom login endpoint `/login.set<timestamp>`.
- **Credentials**: Username and password must be **Base64 encoded**.
- **Login Command**: `#login id=<b64_user> psd=<b64_pass>`
- **Response**: The server returns a JavaScript snippet: `settingsLoginCallback({"status":"1","str":""});`.
    - `status: "1"` = Success
    - `status: "0"` = Failure

### Request Hygiene
- To bypass browser and proxy caching, the device appends a Unix timestamp in milliseconds to every endpoint (e.g., `video_set1733608523271`).

---

## 2. Command Protocol (SET)

Commands are sent via HTTP POST to specific `.set` endpoints. Multiple commands can sometimes be concatenated in a single request body.

### Endpoints
| Endpoint | Description | Example Command |
| :--- | :--- | :--- |
| `video_set` | Routing and Presets | `#video_d out1 matrix=2` |
| `audio_set` | Audio controls | `#audio_d out1 hdmi=1` |
| `input.set` | EDID and Port Names | `#name0 str=MyInput` |
| `ip.set` | Network settings | `#ip dhcp=0` |
| `system_set` | System actions | `#power start=1` |

### Common Command Formats
- **Routing**: `#video_d out<1-4> matrix=<1-4>`. Use `out256` for "All Outputs".
- **Presets**: `#preset:<1-8> exe=<1/0>`. (`1` = Save current routing, `0` = Recall).
- **Audio**: `#audio_d out<1-4> <hdmi/dec>=<1/0>`. (`hdmi` = HDMI audio, `dec` = De-embedded audio).
- **Naming**: `#name<0-15> str=<name>`.
    - 0-3: Inputs
    - 4-7: Outputs
    - 8-15: Presets

---

## 3. Status Retrieval Protocol (GET)

The device uses a highly efficient binary synchronization protocol to minimize bandwidth.

### The Binary Endpoint
Endpoint format: `/binary<crc0>,<crc1>,<crc2>,<crc3>.get<timestamp>`

The client sends 4 CRC32 strings representing its local state of four data blocks.
1. If the client's CRC matches the server's CRC for a block, the server returns a size of `0` for that block and **omits the data**.
2. If the CRCs differ, the server sends the updated block data.

**Initial Request**: Clients usually send `binary12345678,12345678,12345678,12345678` to force the server to send all data initially (since the dummy CRCs won't match).

### Data Packet Structure
The response is a raw byte stream:
1. **Header (16 bytes)**: Four 32-bit unsigned integers (**Little-Endian**). These represent the sizes of Block 0, 1, 2, and 3 in the current payload.
2. **Payload**: The actual bytes for any block with a non-zero size in the header, concatenated in order.

### Block Definitions
- **Block 0 (Network)**: DHCP status, IP, Mask, Gateway, DNS, and MAC.
- **Block 1 (Runtime)**:
    - Video routing matrix.
    - Video ON/OFF states.
    - Audio HDMI/De-embed states.
    - Active EDID indices.
    - Physical port connection status (located at `offset = block_length - 36`).
- **Block 2 (EDID Names)**: 21 fixed-length slots (64 bytes each) containing the text descriptions of EDID profiles.
- **Block 3 (Custom Names)**: 16 fixed-length slots (16 bytes each) for Input, Output, and Preset names.

---

## 4. CRC32 Algorithm

The device uses a custom bitwise CRC32 calculation. **Crucial for maintenance**: If the CRC calculation in the Python client is off by even one bit, the device will re-send the entire binary state every refresh cycle, causing high CPU/Network load.

- **Polynomial**: `0x04C11DB7`
- **Initial Value**: `0xFFFFFFFF`
- **Processing**: Word-by-word (32-bit uints), little-endian byte order.

---

## 5. Implementation Insights (from captures)

### Performance Tuning
The official web app uses an adaptive polling frequency:
- **Fast**: 800ms when data is changing (CRC mismatch detected).
- **Idle**: Slows down to 2000ms and eventually 3000ms if no changes occur over hundreds of cycles.
- **Immediate**: When a command is sent, the timer is cleared and a status request is triggered shortly after to confirm the change.

### Port Status Oddity
Physical cable detection is stored in Block 1 at a negative offset from the end of the block. For a 4x4 matrix, it usually appears in the last 36 bytes of the block.

### Encoding
- All names and strings are **UTF-8** or **ASCII**.
- The server usually replies with `Content-Type: text/html` even for raw binary streams.
- The server is strictly **synchronous**; wait for a response before sending the next command to avoid race conditions in the device's MCU.
