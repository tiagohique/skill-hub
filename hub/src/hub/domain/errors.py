from typing import ClassVar


class HubError(Exception):
    """Erro de domínio. `code` é o identificador estável exposto pela API."""

    code: ClassVar[str] = "hub_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SkillValidationError(HubError):
    code = "invalid_skill"


class LimitExceededError(HubError):
    code = "limit_exceeded"


class VersionConflictError(HubError):
    code = "version_exists"


class InvalidTransitionError(HubError):
    code = "invalid_transition"


class NotFoundError(HubError):
    code = "not_found"


class IntegrityError(HubError):
    code = "integrity_error"


class UnauthorizedError(HubError):
    code = "unauthorized"
