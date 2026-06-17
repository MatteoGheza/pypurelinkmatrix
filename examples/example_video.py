"""Video matrix switching, presets, and port naming."""

import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypurelinkmatrix import PureLinkClient  # noqa: E402
from pypurelinkmatrix.exceptions import DeviceError  # noqa: E402

host = os.getenv("PURELINK_HOST", "127.0.0.1")
port = os.getenv("PURELINK_PORT", "80")
username = os.getenv("PURELINK_USERNAME", "admin")
password = os.getenv("PURELINK_PASSWORD", "password")

host_with_port = f"{host}:{port}" if port != "80" else host

# Video Switching
print("\n=== Video Switching ===")

try:
    with PureLinkClient(host=host_with_port) as client:
        if not client.login(username, password):
            print("✗ Authentication failed")
        else:
            print("✓ Connected")
            print("\nRouting input 2 to output 1...")
            client.video.switch_matrix(output_port=1, input_port=2)
            time.sleep(1)
            print("Routing input 3 to all outputs...")
            client.video.switch_matrix(output_port=0, input_port=3)
            print("✓ Video routing updated")
except DeviceError as e:
    print(f"✗ Error: {e}")

time.sleep(2)

# Preset Management
print("\n=== Preset Management ===")

try:
    with PureLinkClient(host=host_with_port) as client:
        if not client.login(username, password):
            print("✗ Authentication failed")
        else:
            print("✓ Connected")
            print("\nSaving current routing as preset 1...")
            client.video.save_preset(preset_num=1)
            time.sleep(1)
            print("Naming preset...")
            client.video.rename_preset(1, "Conference")
            print("Recalling preset 2...")
            client.video.recall_preset(preset_num=2)

            print("✓ Preset operations completed")
except DeviceError as e:
    print(f"✗ Error: {e}")

time.sleep(1)

# Port Naming
print("\n=== Port Naming ===")

try:
    with PureLinkClient(host=host_with_port) as client:
        if not client.login(username, password):
            print("✗ Authentication failed")
        else:
            print("✓ Connected")
            print("\nNaming inputs...")
            client.video.rename_input(1, "Presenter")
            client.video.rename_input(2, "Document_Camera")

            print("Naming outputs...")
            client.video.rename_output(1, "Main_Display")
            client.video.rename_output(2, "Aux_Display")

            print("Naming presets...")
            client.video.rename_preset(1, "Setup_A")
            client.video.rename_preset(2, "Setup_B")

            print("✓ Port names updated")
except DeviceError as e:
    print(f"✗ Error: {e}")
