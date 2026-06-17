"""Audio output control and configuration."""

import logging
import os
import sys
import time
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

# HDMI Audio Control
print("\n=== HDMI Audio Control ===")

try:
    with PureLinkClient(host=host_with_port) as client:
        if not client.login(username, password):
            print("✗ Authentication failed")
        else:
            print("✓ Connected")
            print("\nEnabling HDMI audio on output 1...")
            client.audio.set_hdmi_output(output=1, enabled=True)
            time.sleep(1)
            print("Disabling HDMI audio on output 2...")
            client.audio.set_hdmi_output(output=2, enabled=False)
            time.sleep(1)
            print("Enabling HDMI audio on all outputs...")
            client.audio.set_hdmi_output(output=0, enabled=True)
            time.sleep(1)
            print("✓ HDMI audio configuration updated")
except DeviceError as e:
    print(f"✗ Error: {e}")

time.sleep(2)

# De-Embed Audio Control
print("\n=== De-Embed Audio Control ===")

try:
    with PureLinkClient(host=host_with_port) as client:
        if not client.login(username, password):
            print("✗ Authentication failed")
        else:
            print("✓ Connected")
            print("\nEnabling de-embed audio on output 1...")
            client.audio.set_de_embed_output(output=1, enabled=True)
            time.sleep(1)
            print("Disabling de-embed on output 2...")
            client.audio.set_de_embed_output(output=2, enabled=False)
            time.sleep(1)
            print("Disabling de-embed on all outputs...")
            client.audio.set_de_embed_output(output=0, enabled=False)
            time.sleep(1)
            print("✓ De-embed audio configuration updated")
except DeviceError as e:
    print(f"✗ Error: {e}")
