"""Complete workflow: Conference room setup."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import aiohttp
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


async def main():
    print("\n" + "=" * 60)
    print("CONFERENCE ROOM SETUP")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        client = PureLinkClient(session, host=host_with_port)

        if not await client.async_login():
            print("✗ Authentication failed")
            return

        print("✓ Connected to device\n")

        try:
            print("1. Configure video routing...")
            await client.video.async_switch_matrix(output_port=1, input_port=1)
            await client.video.async_switch_matrix(output_port=2, input_port=2)
            await client.video.async_switch_matrix(output_port=3, input_port=3)
            await asyncio.sleep(1)

            print("2. Configure audio (HDMI on all outputs)...")
            await client.audio.async_set_hdmi_output(output=0, enabled=True)
            await asyncio.sleep(1)

            print("3. Configure EDID (4K60 LPCM on all inputs)...")
            await client.edid.async_set_input_edid(input_num=0, edid_source=1)
            await asyncio.sleep(1)

            print("4. Name input ports...")
            await client.video.async_rename_input(1, "Presenter")
            await client.video.async_rename_input(2, "Document_Camera")
            await client.video.async_rename_input(3, "Laptop")
            await asyncio.sleep(1)

            print("5. Name output ports...")
            await client.video.async_rename_output(1, "Main_Display")
            await client.video.async_rename_output(2, "Sec_Display")
            await client.video.async_rename_output(3, "Overflow")
            await asyncio.sleep(1)

            print("6. Save preset...")
            await client.video.async_rename_preset(1, "Conference")
            await client.video.async_save_preset(preset_num=1)

            print("\n" + "=" * 60)
            print("✓ Setup Complete!")
            print("Preset 'Conference' saved and ready to use")
            print("=" * 60)
        except DeviceError as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
