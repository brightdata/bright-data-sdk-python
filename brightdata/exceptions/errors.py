class BrightDataError(Exception):
    """Base exception for all Bright Data SDK errors"""
    pass


class ValidationError(BrightDataError):
    """Raised when input validation fails"""
    pass


class AuthenticationError(BrightDataError):
    """Raised when API authentication fails"""
    pass


class ZoneError(BrightDataError):
    """Raised when zone operations fail"""
    pass


class NetworkError(BrightDataError):
    """Raised when network operations fail"""
    pass


class APIError(BrightDataError):
    """Raised when API requests fail"""
    def __init__(self, message, status_code=None, response_text=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text