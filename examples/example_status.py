"""Example: Query device status and current routing."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypurelinkmatrix import PureLinkClient  # noqa: E402
from pypurelinkmatrix.exceptions import DeviceError  # noqa: E402

# Load environment variables
load_dotenv()

# Configuration from environment variables
host = os.getenv("PURELINK_HOST", "127.0.0.1")
port = os.getenv("PURELINK_PORT", "80")
username = os.getenv("PURELINK_USERNAME", "admin")
password = os.getenv("PURELINK_PASSWORD", "password")

# Handle port if not default 80
host_with_port = f"{host}:{port}" if port != "80" else host


def query_all_status():
    """Query complete device status."""
    print("\n=== Device Status ===")
    client = PureLinkClient(host=host_with_port)

    try:
        if not client.login(username, password):
            print("✗ Authentication failed")
            return

        # Video routing
        routing = client.status.get_video_routing()
        print("\n✓ Video routing:")
        for output, input_port in routing.items():
            print(f"  Output {output} ← Input {input_port}")

        # Audio state
        audio = client.status.get_audio_output_state()
        print("\n✓ Audio state:")
        for output, state in audio.items():
            hdmi = "ON" if state.get("hdmi") else "OFF"
            embed = "ON" if state.get("de_embed") else "OFF"
            print(f"  Output {output}: HDMI={hdmi}, De-Embed={embed}")

        # EDID configuration
        edid = client.status.get_edid_configuration()
        print("\n✓ EDID configuration:")
        for input_num, config in edid.items():
            print(f"  Input {input_num}: {config.get('name')}")

        # Port names
        names = client.status.get_port_names()
        print("\n✓ Port names:")
        print(f"  Inputs: {names.get('inputs', {})}")
        print(f"  Outputs: {names.get('outputs', {})}")
        print(f"  Presets: {names.get('presets', {})}")

    except DeviceError as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    print("PureLink Device Status")
    print("=" * 50)
    query_all_status()
    print("\n" + "=" * 50)
    print("Update host/credentials to test against your device")
