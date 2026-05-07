"""Domain exceptions — raised by services, translated to HTTP by global handlers."""


class AppError(Exception):
    """Base for all application domain exceptions."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    """Resource does not exist (→ 404)."""


class ConflictError(AppError):
    """Unique-constraint violation or duplicate resource (→ 409)."""


class AuthenticationError(AppError):
    """Invalid credentials or expired token (→ 401)."""


class ForbiddenError(AppError):
    """Caller lacks permission for the resource (→ 403)."""


class DomainValidationError(AppError):
    """Business-rule validation failed (→ 400)."""
