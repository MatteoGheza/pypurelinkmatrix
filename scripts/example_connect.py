"""Example script for connecting to PureLink matrix device."""

import logging
import sys
from pathlib import Path

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypurelinkmatrix import PureLinkClient  # noqa: E402
from pypurelinkmatrix.exceptions import (  # noqa: E402
    AuthenticationError,
    PureLinkConnectionError,
    ValidationError,
)


def example_basic_login():
    """Example: Basic login to device."""
    print("\n=== Example 1: Basic Login ===")

    # Create client
    client = PureLinkClient(
        host="192.168.1.100",  # Replace with actual device IP
        username="admin",  # Replace with actual username
        password="password",  # Replace with actual password
    )

    try:
        # Attempt login
        if client.login():
            print(f"✓ Successfully authenticated: {client}")
        else:
            print("✗ Authentication failed")

    except ValidationError as e:
        print(f"✗ Validation error: {e}")
    except AuthenticationError as e:
        print(f"✗ Authentication error: {e}")
    except PureLinkConnectionError as e:
        print(f"✗ Connection error: {e}")
    finally:
        client.close()


def example_context_manager():
    """Example: Using context manager for automatic cleanup."""
    print("\n=== Example 2: Context Manager ===")

    try:
        with PureLinkClient(host="192.168.1.100") as client:
            if client.login("admin", "password"):
                print(f"✓ Connected: {client}")
                # Perform operations here
                print("✓ Session is active")
            # Automatic cleanup on exit

    except Exception as e:
        print(f"✗ Error: {e}")


def example_credentials_at_login():
    """Example: Providing credentials at login time."""
    print("\n=== Example 3: Credentials at Login Time ===")

    # Create client without credentials
    client = PureLinkClient(host="192.168.1.100")

    try:
        # Provide credentials at login
        if client.login(username="admin", password="password"):
            print(f"✓ Authenticated with login-time credentials: {client}")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()


def example_input_validation():
    """Example: Input validation in action."""
    print("\n=== Example 4: Input Validation ===")

    # Test various invalid inputs
    invalid_credentials = [
        ("", "password"),  # Empty username
        ("admin", ""),  # Empty password
        ("admin_with_special_chars!", "password"),  # Invalid characters
        ("username_too_long_more_than_15_chars", "password"),  # Too long
        ("admin", "password_too_long_more_than_15"),  # Password too long
    ]

    for username, password in invalid_credentials:
        try:
            client = PureLinkClient(host="192.168.1.100")
            client.login(username, password)
        except ValidationError as e:
            print(f"✓ Caught validation error: {e}")
        finally:
            client.close()


if __name__ == "__main__":
    print("PyPureLink Matrix - Connection Examples")
    print("=" * 50)

    # Uncomment the example you want to run:

    # example_basic_login()
    # example_context_manager()
    # example_credentials_at_login()
    example_input_validation()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: Replace IP addresses and credentials with actual values")
    print("to test against a real PureLink device.")
