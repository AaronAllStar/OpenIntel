class DomainError(Exception):
    """Base class for all domain errors."""


class ValidationError(DomainError):
    """Raised when an entity or value object fails invariant validation."""


class TargetValidationError(ValidationError):
    """Raised when a target fails format or security validation (e.g. SSRF)."""


class InvestigationNotFoundError(DomainError):
    """Raised when an investigation is requested but does not exist."""


class InvalidStateTransitionError(DomainError):
    """Raised when an investigation transitions between invalid lifecycle states."""


class AdapterError(DomainError):
    """Raised when an adapter fails or times out."""
