"""Complete workflow: Conference room setup."""

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

print("\n" + "=" * 60)
print("CONFERENCE ROOM SETUP")
print("=" * 60)

try:
    with PureLinkClient(host=host_with_port) as client:
        if not client.login(username, password):
            print("✗ Authentication failed")
        else:
            print("✓ Connected to device\n")

            print("1. Configure video routing...")
            client.video.switch_matrix(output_port=1, input_port=1)
            client.video.switch_matrix(output_port=2, input_port=2)
            client.video.switch_matrix(output_port=3, input_port=3)
            time.sleep(1)

            print("2. Configure audio (HDMI on all outputs)...")
            client.audio.set_hdmi_output(output=0, enabled=True)
            time.sleep(1)

            print("3. Configure EDID (4K60 LPCM on all inputs)...")
            client.edid.set_input_edid(input_num=0, edid_source=1)
            time.sleep(1)

            print("4. Name input ports...")
            client.video.rename_input(1, "Presenter")
            client.video.rename_input(2, "Document_Camera")
            client.video.rename_input(3, "Laptop")
            time.sleep(1)

            print("5. Name output ports...")
            client.video.rename_output(1, "Main_Display")
            client.video.rename_output(2, "Sec_Display")
            client.video.rename_output(3, "Overflow")
            time.sleep(1)

            print("6. Save preset...")
            client.video.rename_preset(1, "Conference")
            client.video.save_preset(preset_num=1)

            print("\n" + "=" * 60)
            print("✓ Setup Complete!")
            print("Preset 'Conference' saved and ready to use")
            print("=" * 60)
except DeviceError as e:
    print(f"✗ Error: {e}")
