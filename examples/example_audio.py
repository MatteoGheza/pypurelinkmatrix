"""Audio output control and configuration."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import aiohttp
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

        # HDMI Audio Control
        print("\n=== HDMI Audio Control ===")
        try:
            print("\nEnabling HDMI audio on output 1...")
            await client.audio.async_set_hdmi_output(output=1, enabled=True)
            await asyncio.sleep(1)
            print("Disabling HDMI audio on output 2...")
            await client.audio.async_set_hdmi_output(output=2, enabled=False)
            await asyncio.sleep(1)
            print("Enabling HDMI audio on all outputs...")
            await client.audio.async_set_hdmi_output(output=0, enabled=True)
            await asyncio.sleep(1)
            print("✓ HDMI audio configuration updated")
        except DeviceError as e:
            print(f"✗ Error: {e}")

        await asyncio.sleep(2)

        # De-Embed Audio Control
        print("\n=== De-Embed Audio Control ===")
        try:
            print("\nEnabling de-embed audio on output 1...")
            await client.audio.async_set_de_embed_output(output=1, enabled=True)
            await asyncio.sleep(1)
            print("Disabling de-embed on output 2...")
            await client.audio.async_set_de_embed_output(output=2, enabled=False)
            await asyncio.sleep(1)
            print("Disabling de-embed on all outputs...")
            await client.audio.async_set_de_embed_output(output=0, enabled=False)
            await asyncio.sleep(1)
            print("✓ De-embed audio configuration updated")
        except DeviceError as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
