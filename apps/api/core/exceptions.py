# Defines custom application errors (e.g., AuthError, NotFoundError) and ensures all API errors return a consistent JSON response format.


from typing import Any, Dict, Optional

class AppError(Exception):
    """Base exception for all application errors."""
    status_code: int = 500
    code: str = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class NotFoundError(AppError):
    """Raised when a requested resource is not found."""
    status_code: int = 404
    code: str = "NOT_FOUND"

class ValidationError(AppError):
    """Raised when request validation fails."""
    status_code: int = 400
    code: str = "VALIDATION_ERROR"

class AuthError(AppError):
    """Raised when authentication or authorization fails."""
    status_code: int = 401
    code: str = "UNAUTHORIZED"

class ApprovalRequiredError(AppError):
    """Raised when an agent action requires explicit human approval to proceed."""
    status_code: int = 403
    code: str = "APPROVAL_REQUIRED"

class ExternalServiceError(AppError):
    """Raised when an external API / service (OpenAI, Google, ElevenLabs, etc.) fails."""
    status_code: int = 502
    code: str = "EXTERNAL_SERVICE_ERROR"

class RateLimitError(AppError):
    """Raised when client exceeds rate limits."""
    status_code: int = 429
    code: str = "RATE_LIMIT_EXCEEDED"
