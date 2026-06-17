"""EDID profile configuration and management."""

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
        client = PureLinkClient(session, host=host_with_port)

        if not await client.async_login():
            print("✗ Authentication failed")
            return

        print("✓ Connected")

        # Set Input EDID
        print("\n=== Set Input EDID ===")
        try:
            print("\nSetting EDID profile 1 (4K60 LPCM) on input 1...")
            await client.edid.async_set_input_edid(input_num=1, edid_source=1)
            await asyncio.sleep(1)
            print("Setting EDID profile 3 on input 2...")
            await client.edid.async_set_input_edid(input_num=2, edid_source=3)
            await asyncio.sleep(1)
            print("Setting EDID profile 1 on all inputs...")
            await client.edid.async_set_input_edid(input_num=0, edid_source=1)
            await asyncio.sleep(1)
            print("✓ Input EDID profiles configured")
        except DeviceError as e:
            print(f"✗ Error: {e}")

        await asyncio.sleep(2)

        # User EDID Management
        print("\n=== User EDID Management ===")
        try:
            print("\nCopying standard profile 1 to user slot 1...")
            await client.edid.async_set_user_edid(source_profile=1, destination=1)
            await asyncio.sleep(1)
            print("Copying standard profile 4 to user slot 2...")
            await client.edid.async_set_user_edid(source_profile=4, destination=2)
            await asyncio.sleep(1)
            print("Copying profile to all user slots...")
            await client.edid.async_set_user_edid(source_profile=1, destination=0)
            await asyncio.sleep(1)
            print("✓ User EDID profiles updated")
        except DeviceError as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
