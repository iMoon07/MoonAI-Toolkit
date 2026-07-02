class MoonCoreException(Exception):
    """Base exception for all moon_core errors."""
    pass

class ConfigurationError(MoonCoreException):
    """Raised when environment variables or settings are missing/invalid."""
    pass

class APIConnectionError(MoonCoreException):
    """Raised when the LLM API is unreachable."""
    pass

class APITimeoutError(MoonCoreException):
    """Raised when the LLM API takes too long to respond."""
    pass
