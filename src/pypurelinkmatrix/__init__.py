"""PyPureLink Matrix - Python library for PureLink matrix device management."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("pypurelinkmatrix")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.1"

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
