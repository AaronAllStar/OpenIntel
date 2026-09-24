import logging
from typing import Any

import structlog

from src.app.infrastructure.config import get_settings

REDACT_KEYS = {"password", "token", "secret", "key", "authorization", "api_key"}


def redact_sensitive_keys(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    for k in list(event_dict.keys()):
        if any(sensitive in k.lower() for sensitive in REDACT_KEYS):
            event_dict[k] = "[REDACTED]"
    return event_dict


def setup_logging() -> None:
    settings = get_settings()
    log_level = logging.DEBUG if settings.DEBUG and settings.ENV != "prod" else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            redact_sensitive_keys,
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger()
