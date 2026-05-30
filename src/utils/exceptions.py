class AmgenPOCError(Exception):
    """Base exception for all application errors."""


class NotFoundError(AmgenPOCError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} with id '{identifier}' not found.")


class ValidationError(AmgenPOCError):
    """Raised when input data fails validation."""

    def __init__(self, message: str):
        super().__init__(message)


class DatabaseError(AmgenPOCError):
    """Raised when a database operation fails."""

    def __init__(self, message: str, original: Exception = None):
        self.original = original
        super().__init__(message)
