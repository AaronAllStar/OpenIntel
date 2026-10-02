import logging
import re
from typing import Any

import structlog

from src.app.infrastructure.config import get_settings

REDACT_KEYS = {"password", "token", "secret", "key", "authorization", "api_key", "national_id"}
EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*(@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
PHONE_REGEX = re.compile(r"(\+?[0-9]{1,3}[-.\s]?\(?[0-9]{3}\)?[-.\s]?)[0-9]{3,4}([-.\s]?[0-9]{3,4})")



def mask_pii_string(val: str) -> str:
    """Mask email addresses and phone numbers in log messages."""
    val = EMAIL_REGEX.sub(r"\1***\2", val)
    return PHONE_REGEX.sub(r"\1***\2", val)


def redact_sensitive_keys(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    for k in list(event_dict.keys()):
        if any(sensitive in k.lower() for sensitive in REDACT_KEYS):
            event_dict[k] = "[REDACTED]"
        elif isinstance(event_dict[k], str):
            event_dict[k] = mask_pii_string(event_dict[k])
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
