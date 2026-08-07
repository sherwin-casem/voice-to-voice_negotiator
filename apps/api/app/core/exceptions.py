class AppError(Exception):
    """Base application error mapped to structured API responses."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__("NOT_FOUND", message, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("CONFLICT", message, status_code=409)


class MaxQuestionsReachedError(AppError):
    """The configured question budget is exhausted; the session should end."""

    def __init__(self, message: str = "Maximum question count reached") -> None:
        super().__init__("MAX_QUESTIONS_REACHED", message, status_code=409)


class InvalidStateError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_STATE", message, status_code=409)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__("UNAUTHORIZED", message, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__("FORBIDDEN", message, status_code=403)


class RateLimitedError(AppError):
    def __init__(self, message: str = "Too many requests, please retry later") -> None:
        super().__init__("RATE_LIMITED", message, status_code=429)
