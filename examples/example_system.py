"""System administration and user management."""

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

        # Change Admin Password
        print("\n=== Change Admin Password ===")
        try:
            print("\nChanging admin password...")
            await client.system.async_change_password(username="admin", password="newpass123")
            print("✓ Password updated (remember to login with new password)")
        except DeviceError as e:
            print(f"✗ Error: {e}")

        await asyncio.sleep(1)

        # Create Operator User
        print("\n=== Create Operator User ===")
        try:
            print("\nCreating operator user account...")
            await client.system.async_change_password(username="operator", password="op_pass123")
            print("✓ Operator account created (username: operator)")
        except DeviceError as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
