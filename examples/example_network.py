"""Network configuration and IP management."""

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

        # Static IP Configuration
        print("\n=== Static IP Configuration ===")
        try:
            print("\nConfiguring static IP address...")
            await client.network.async_configure_static_ip(
                ip_address="192.168.1.150",
                subnet_mask="255.255.255.0",
                gateway="192.168.1.1",
            )
            print("✓ Static IP configured (192.168.1.150)")
        except (DeviceError, ValueError) as e:
            print(f"✗ Error: {e}")

        await asyncio.sleep(1)

        # DHCP Configuration
        print("\n=== DHCP Configuration ===")
        try:
            print("\nEnabling DHCP...")
            await client.network.async_enable_dhcp()
            print("✓ DHCP enabled (device will receive IP from DHCP server)")
        except DeviceError as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
