"""CoinGecko provider exceptions."""


class CoinGeckoError(Exception):
    """Base exception for CoinGecko provider operations."""
    pass


class CoinGeckoConfigurationError(CoinGeckoError):
    """Raised when CoinGecko settings or credentials are missing or invalid."""
    pass


class CoinGeckoAuthenticationError(CoinGeckoError):
    """Raised when authentication with CoinGecko API fails (HTTP 401/403)."""
    pass


class CoinGeckoRateLimitError(CoinGeckoError):
    """Raised when CoinGecko returns rate limit response (HTTP 429)."""
    pass


class CoinGeckoNotFoundError(CoinGeckoError):
    """Raised when coin or endpoint is not found (HTTP 404)."""
    pass


class CoinGeckoAPIError(CoinGeckoError):
    """Raised when CoinGecko API returns an unexpected error or bad payload."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
