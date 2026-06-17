"""PyPureLink Matrix - Python library for PureLink matrix device management."""

__version__ = "0.1.0"

from .auth import PureLinkAuth
from .client import PureLinkClient
from .exceptions import (
    AuthenticationError,
    DeviceError,
    PureLinkConnectionError,
    PureLinkError,
    ValidationError,
)
from .models import (
    AudioState,
    DeviceState,
    EDIDState,
    NetworkState,
    PortNames,
    VideoMatrixState,
)

__all__ = [
    "PureLinkAuth",
    "PureLinkClient",
    "DeviceState",
    "VideoMatrixState",
    "AudioState",
    "EDIDState",
    "NetworkState",
    "PortNames",
    "PureLinkError",
    "PureLinkConnectionError",
    "AuthenticationError",
    "ValidationError",
    "DeviceError",
]
