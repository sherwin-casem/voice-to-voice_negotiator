class AIProviderError(Exception):
    """Base error for AI provider failures."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        super().__init__(message)


class AIConfigurationError(AIProviderError):
    def __init__(self, message: str) -> None:
        super().__init__("AI_CONFIGURATION_ERROR", message, retryable=False)


class AIAuthenticationError(AIProviderError):
    def __init__(self, message: str = "AI provider authentication failed") -> None:
        super().__init__("AI_AUTHENTICATION_ERROR", message, retryable=False, status_code=401)


class AIRateLimitError(AIProviderError):
    def __init__(self, message: str = "AI provider rate limit exceeded") -> None:
        super().__init__("AI_RATE_LIMIT", message, retryable=True, status_code=429)


class AITimeoutError(AIProviderError):
    def __init__(self, message: str = "AI provider request timed out") -> None:
        super().__init__("AI_TIMEOUT", message, retryable=True)


class AIConnectionError(AIProviderError):
    def __init__(self, message: str = "AI provider connection failed") -> None:
        super().__init__("AI_CONNECTION_ERROR", message, retryable=True)


class AIResponseError(AIProviderError):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__("AI_RESPONSE_ERROR", message, retryable=retryable)


class AIUnavailableError(AIProviderError):
    def __init__(self, message: str = "AI provider temporarily unavailable") -> None:
        super().__init__("AI_UNAVAILABLE", message, retryable=True, status_code=503)
