"""Example: Status update manager with callbacks."""

import logging
import os
import time

from dotenv import load_dotenv
from pypurelinkmatrix import PureLinkClient
from pypurelinkmatrix.api import StatusUpdateManager

# Load environment variables
load_dotenv()

# Configuration from environment variables
host = os.getenv("PURELINK_HOST", "127.0.0.1")
port = os.getenv("PURELINK_PORT", "80")
username = os.getenv("PURELINK_USERNAME", "admin")
password = os.getenv("PURELINK_PASSWORD", "password")

# Handle port if not default 80
host_with_port = f"{host}:{port}" if port != "80" else host

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def on_network_update(block_num: int, data: bytes, size: int) -> None:
    """Network/IP data updated."""
    logger.info(f"[Block 0] Network data updated ({size} bytes)")


def on_runtime_update(block_num: int, data: bytes, size: int) -> None:
    """Runtime state updated (video, audio, EDID)."""
    logger.info(f"[Block 1] Runtime data updated ({size} bytes)")


def on_edid_names_update(block_num: int, data: bytes, size: int) -> None:
    """EDID name/label updated."""
    logger.info(f"[Block 2] EDID names updated ({size} bytes)")


def on_port_names_update(block_num: int, data: bytes, size: int) -> None:
    """Port and preset names updated."""
    logger.info(f"[Block 3] Port/preset names updated ({size} bytes)")


def main():
    """Run status update manager with callbacks."""
    client = PureLinkClient(host=host_with_port)

    # Login to device
    if not client.login(username, password):
        logger.error("Authentication failed")
        return

    logger.info("Creating status update manager...")
    update_manager = StatusUpdateManager(
        session=client.session,
        base_url=client._base_url,
        initial_fresh_time=800,
    )

    logger.info("Registering callbacks...")
    update_manager.register_callback(0, on_network_update)
    update_manager.register_callback(1, on_runtime_update)
    update_manager.register_callback(2, on_edid_names_update)
    update_manager.register_callback(3, on_port_names_update)

    logger.info("Starting updates...")
    update_manager.start_updates()

    try:
        logger.info("Updates running... (10 seconds)")
        for i in range(10):
            time.sleep(1)
            if i % 3 == 0:
                state = update_manager.get_state()
                logger.info(f"IP: {state.ip.ip}, Video: {state.run.video_mx}")

    except KeyboardInterrupt:
        logger.info("Stopped by user")

    finally:
        logger.info("Stopping updates...")
        update_manager.stop_updates()

        state = update_manager.get_state()
        logger.info(f"Final state - IP: {state.ip.ip}, DHCP: {state.ip.dhcp}")

        client.close()


if __name__ == "__main__":
    main()
