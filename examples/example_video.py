"""Video matrix switching, presets, and port naming."""

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
    async with aiohttp.ClientSession() as session:
        client = PureLinkClient(
            session,
            host=host_with_port,
            username=username,
            password=password,
        )

        if not await client.async_login():
            print("✗ Authentication failed")
            return

        print("✓ Connected")

        # Video Switching
        print("\n=== Video Switching ===")
        try:
            print("\nRouting input 2 to output 1...")
            await client.video.async_switch_matrix(output_port=1, input_port=2)
            await asyncio.sleep(1)
            print("Routing input 3 to all outputs...")
            await client.video.async_switch_matrix(output_port=0, input_port=3)
            print("✓ Video routing updated")
        except DeviceError as e:
            print(f"✗ Error: {e}")

        await asyncio.sleep(2)

        # Preset Management
        print("\n=== Preset Management ===")
        try:
            print("\nSaving current routing as preset 1...")
            await client.video.async_save_preset(preset_num=1)
            await asyncio.sleep(1)
            print("Naming preset...")
            await client.video.async_rename_preset(1, "Conference")
            print("Recalling preset 2...")
            await client.video.async_recall_preset(preset_num=2)

            print("✓ Preset operations completed")
        except DeviceError as e:
            print(f"✗ Error: {e}")

        await asyncio.sleep(1)

        # Port Naming
        print("\n=== Port Naming ===")
        try:
            print("\nNaming inputs...")
            await client.video.async_rename_input(1, "Presenter")
            await client.video.async_rename_input(2, "Document_Camera")

            print("Naming outputs...")
            await client.video.async_rename_output(1, "Main_Display")
            await client.video.async_rename_output(2, "Aux_Display")

            print("Naming presets...")
            await client.video.async_rename_preset(1, "Setup_A")
            await client.video.async_rename_preset(2, "Setup_B")

            print("✓ Port names updated")
        except DeviceError as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
