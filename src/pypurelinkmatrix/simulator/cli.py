"""CLI for PureLink Matrix Simulator."""

import threading

import uvicorn

from .server import app, simulator
from .tui import run_tui


def main():
    """Start the simulator server and TUI."""
    # Run FastAPI in a background thread
    server_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": "0.0.0.0", "port": 8000, "log_level": "error"},
        daemon=True,
    )
    server_thread.start()

    # Run the TUI in the main thread
    try:
        run_tui(simulator)
    except KeyboardInterrupt:
        print("\nStopping simulator...")


if __name__ == "__main__":
    main()
