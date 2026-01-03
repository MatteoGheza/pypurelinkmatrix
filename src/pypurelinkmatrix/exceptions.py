"""Exceptions for PyPureLink Matrix library."""


class PureLinkError(Exception):
    """Base exception for PyPureLink Matrix."""

    pass


class PureLinkConnectionError(PureLinkError):
    """Raised when connection to device fails."""

    pass


class AuthenticationError(PureLinkError):
    """Raised when authentication fails."""

    pass


class ValidationError(PureLinkError):
    """Raised when input validation fails."""

    pass


class DeviceError(PureLinkError):
    """Raised when device returns an error."""

    pass
