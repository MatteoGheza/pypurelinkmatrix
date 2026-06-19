"""Example: Connecting to PureLink matrix device (Async)."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypurelinkmatrix import PureLinkClient  # noqa: E402
from pypurelinkmatrix.exceptions import (  # noqa: E402
    AuthenticationError,
    PureLinkConnectionError,
    ValidationError,
)

# Load environment variables
load_dotenv()

# Configuration from environment variables
host = os.getenv("PURELINK_HOST", "127.0.0.1")
port = os.getenv("PURELINK_PORT", "80")
username = os.getenv("PURELINK_USERNAME", "admin")
password = os.getenv("PURELINK_PASSWORD", "password")

# Handle port if not default 80
host_with_port = f"{host}:{port}" if port != "80" else host


async def example_basic_login():
    """Basic login to device."""
    print("\n=== Basic Login ===")
    async with aiohttp.ClientSession() as session:
        client = PureLinkClient(
            session,
            host=host_with_port,
            username=username,
            password=password,
        )
        try:
            if await client.async_login():
                print(f"✓ Authenticated: {client}")
            else:
                print("✗ Authentication failed")
        except (ValidationError, AuthenticationError, PureLinkConnectionError) as e:
            print(f"✗ Error: {e}")


async def example_input_validation():
    """Input validation examples."""
    print("\n=== Input Validation ===")
    invalid = [
        ("", "password"),
        ("admin_with_special!", "password"),
        ("admin_too_long_more_than_15", "password"),
    ]

    async with aiohttp.ClientSession() as session:
        for u, p in invalid:
            try:
                client = PureLinkClient(session, host=host_with_port, username=u, password=p)
                await client.async_login()
            except ValidationError as e:
                print(f"✓ Caught: {e}")


async def main():
    """Run all examples."""
    await example_basic_login()
    await example_input_validation()


if __name__ == "__main__":
    asyncio.run(main())
