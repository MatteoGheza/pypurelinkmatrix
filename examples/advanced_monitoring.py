"""Monitor device state and detect routing changes."""

import asyncio
import logging
import os
from typing import Optional

import aiohttp
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceMonitor:
    """Detect video routing, audio, and port connection changes."""

    def __init__(self, client: PureLinkClient):
        """Initialize monitor with PureLink client."""
        self.client = client
        self.manager = StatusUpdateManager(
            auth=client.auth,
            initial_fresh_time=800,
        )

        self.prev_video_mx: Optional[list[int]] = None
        self.prev_audio_hdmi: Optional[list[int]] = None
        self.prev_port_status: Optional[tuple[list[int], list[int]]] = None

        self.manager.register_callback(1, self._on_runtime_update)

    def _on_runtime_update(self, block: int, data: bytes, size: int) -> None:
        """Handle runtime state changes."""
        # Note: StatusUpdateManager.get_state() is now sync, but should probably be awaited if async
        # However, looking at status_update_manager.py, it is a normal method returning deepcopy.
        state = self.manager.web_data

        if self.prev_video_mx != state.run.video_mx:
            logger.info("🎬 Video Routing Changed:")
            for output in range(1, 5):
                input_port = state.run.video_mx[output - 1]
                logger.info(
                    f"   Output {output} → Input {input_port}"
                    if input_port > 0
                    else f"   Output {output} → No Input"
                )
            self.prev_video_mx = state.run.video_mx.copy()

        if self.prev_audio_hdmi != state.run.audio_hdmi:
            logger.info("🔊 Audio State Changed:")
            for output in range(1, 5):
                hdmi = bool(state.run.audio_hdmi[output - 1])
                deembed = bool(state.run.audio_dec[output - 1])
                logger.info(f"   Output {output}: HDMI={hdmi}, De-embed={deembed}")
            self.prev_audio_hdmi = state.run.audio_hdmi.copy()

        if self.prev_port_status != (
            state.run.in_port_status,
            state.run.out_port_status,
        ):
            logger.info("🔌 Port Connection Status Changed:")
            for port in range(1, 5):
                status = "Connected" if state.run.in_port_status[port - 1] else "Disconnected"
                logger.info(f"   Input {port}: {status}")
            for port in range(1, 5):
                status = "Connected" if state.run.out_port_status[port - 1] else "Disconnected"
                logger.info(f"   Output {port}: {status}")
            self.prev_port_status = (
                state.run.in_port_status.copy(),
                state.run.out_port_status.copy(),
            )

    def start(self) -> None:
        """Start monitoring."""
        logger.info("Starting device monitor...")
        self.manager.start_updates()

    def stop(self) -> None:
        """Stop monitoring."""
        logger.info("Stopping device monitor...")
        self.manager.stop_updates()

    async def print_status(self) -> None:
        """Print current device status."""
        state = await self.manager.async_get_state()

        logger.info("=" * 60)
        logger.info("DEVICE STATUS")
        logger.info("=" * 60)

        logger.info("Network Configuration:")
        logger.info(f"  IP: {state.ip.ip}, Mask: {state.ip.mask}")
        logger.info(f"  Gateway: {state.ip.gw}, DNS: {state.ip.dns}")
        logger.info(f"  MAC: {state.ip.mac}, DHCP: {bool(state.ip.dhcp)}")

        logger.info("Video Matrix:")
        for output in range(1, 5):
            input_port = state.run.video_mx[output - 1]
            logger.info(f"  Output {output} ← Input {input_port}")

        logger.info("Audio:")
        for output in range(1, 5):
            hdmi = "ON" if state.run.audio_hdmi[output - 1] else "OFF"
            deembed = "ON" if state.run.audio_dec[output - 1] else "OFF"
            logger.info(f"  Output {output}: HDMI={hdmi}, De-embed={deembed}")

        logger.info("Port Names:")
        for i, name in enumerate(state.name.port_name, 1):
            if i <= 4:
                logger.info(f"  Input {i}: {name or 'Not set'}")
            else:
                logger.info(f"  Output {i - 4}: {name or 'Not set'}")

        logger.info("=" * 60)


class PeriodicStatusReporter:
    """Report device status at regular intervals."""

    def __init__(self, manager: StatusUpdateManager, interval: int = 30):
        """Initialize reporter with update interval in seconds."""
        self.manager = manager
        self.interval = interval
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Start periodic reporting."""
        self._stop_event.clear()
        self._task = asyncio.create_task(self._report_loop())
        logger.info(f"Started periodic reporter (every {self.interval}s)")

    def stop(self) -> None:
        """Stop periodic reporting."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
        logger.info("Stopped periodic reporter")

    async def _report_loop(self) -> None:
        """Background loop for periodic reporting."""
        while not self._stop_event.is_set():
            state = await self.manager.async_get_state()
            logger.info(f"📊 IP: {state.ip.ip} | Video: {state.run.video_mx}")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                continue


async def main():
    """Run advanced monitoring."""
    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Connecting to {host_with_port}...")
            client = PureLinkClient(session, host=host_with_port)

            if not await client.async_login():
                logger.error("Authentication failed")
                return 1

            monitor = DeviceMonitor(client)
            reporter = PeriodicStatusReporter(manager=monitor.manager, interval=15)

            monitor.start()
            reporter.start()

            try:
                logger.info("Waiting for status update...")
                await asyncio.sleep(2)
                await monitor.print_status()

                logger.info("Monitoring (press Ctrl+C to stop)...")
                while True:
                    await asyncio.sleep(1)

            except KeyboardInterrupt:
                logger.info("Stopped by user")

            finally:
                reporter.stop()
                monitor.stop()
                await monitor.print_status()
                logger.info("Monitor closed")

        except Exception as e:
            logger.error(f"Error: {e}")
            return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
