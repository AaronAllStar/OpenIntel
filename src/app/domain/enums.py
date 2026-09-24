from enum import StrEnum


class TargetKind(StrEnum):
    USERNAME = "username"
    EMAIL = "email"
    DOMAIN = "domain"
    URL = "url"
    IP = "ip"
    ORGANIZATION = "organization"
    PHONE = "phone"
    NATIONAL_ID = "national_id"
    REPOSITORY = "repository"
    PERSON_NAME = "person_name"
    LOCATION = "location"


class InvestigationType(StrEnum):
    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"


class InvestigationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WORKING = "working"
    REVIEW = "review"
    FINAL = "final"
    CANCELLED = "cancelled"
    ERROR = "error"


class ConfidenceLevel(StrEnum):
    OBSERVED = "observed"
    SUPPORTED = "supported"
    POTENTIAL = "potential"
    STRONG = "strong"


class InfoClassification(StrEnum):
    PUBLIC_OBSERVATION = "PUBLIC_OBSERVATION"
    PUBLIC_REGISTRY = "PUBLIC_REGISTRY"
    PLATFORM_SIGNAL = "PLATFORM_SIGNAL"
    INFERENCE = "INFERENCE"


class EntityKind(StrEnum):
    PROFILE = "profile"
    EMAIL = "email"
    DOMAIN = "domain"
    IP = "ip"
    URL = "url"
    ORGANIZATION = "organization"
    PHONE = "phone"
    DOCUMENT = "document"
    PERSON = "person"
    NATIONAL_ID = "national_id"
    REPOSITORY = "repository"
    LOCATION = "location"
