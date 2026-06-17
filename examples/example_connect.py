"""Example: Connecting to PureLink matrix device."""

import logging
import os
import sys
from pathlib import Path

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


def example_basic_login():
    """Basic login to device."""
    print("\n=== Basic Login ===")
    client = PureLinkClient(host=host_with_port)
    try:
        if client.login(username, password):
            print(f"✓ Authenticated: {client}")
        else:
            print("✗ Authentication failed")
    except (ValidationError, AuthenticationError, PureLinkConnectionError) as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()


def example_context_manager():
    """Using context manager for automatic cleanup."""
    print("\n=== Context Manager ===")
    try:
        with PureLinkClient(host=host_with_port) as client:
            if client.login(username, password):
                print("✓ Connected")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_credentials_at_login():
    """Providing credentials at login time."""
    print("\n=== Credentials at Login ===")
    client = PureLinkClient(host=host_with_port)
    try:
        if client.login(username=username, password=password):
            print("✓ Authenticated")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()


def example_input_validation():
    """Input validation examples."""
    print("\n=== Input Validation ===")
    invalid = [
        ("", "password"),
        ("admin_with_special!", "password"),
        ("admin_too_long_more_than_15", "password"),
    ]

    for u, p in invalid:
        try:
            client = PureLinkClient(host=host_with_port)
            client.login(u, p)
        except ValidationError as e:
            print(f"✓ Caught: {e}")
        finally:
            client.close()


# Uncomment to run:
# example_basic_login()
# example_context_manager()
# example_credentials_at_login()
example_input_validation()
