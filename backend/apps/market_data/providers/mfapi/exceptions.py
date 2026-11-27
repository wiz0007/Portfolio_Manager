"""MFAPI exceptions."""


class MFAPIError(Exception):
    """Base exception for MFAPI provider operations."""
    pass


class MFAPINotFoundError(MFAPIError):
    """Raised when a mutual fund scheme code is not found."""
    pass


class MFAPIConnectionError(MFAPIError):
    """Raised when connection to MFAPI fails or times out."""
    pass
