import ipaddress
import re
import urllib.parse
from dataclasses import dataclass
from uuid import UUID

from src.app.domain.enums import TargetKind
from src.app.domain.errors import TargetValidationError

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$"
)


def _is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class Target:
    kind: TargetKind
    value: str
    allow_private: bool = False

    def __post_init__(self) -> None:
        trimmed = self.value.strip()
        if not trimmed:
            raise TargetValidationError("Target value cannot be empty")

        match self.kind:
            case TargetKind.USERNAME:
                if not USERNAME_REGEX.match(trimmed):
                    raise TargetValidationError(
                        f"Invalid username '{trimmed}'. Must match {USERNAME_REGEX.pattern}"
                    )

            case TargetKind.EMAIL:
                if len(trimmed) > 254 or not EMAIL_REGEX.match(trimmed):
                    raise TargetValidationError(f"Invalid email address '{trimmed}'")

            case TargetKind.DOMAIN:
                try:
                    # IDNA normalization check
                    encoded = trimmed.encode("idna").decode("ascii")
                except Exception as exc:
                    raise TargetValidationError(f"Invalid IDNA domain '{trimmed}'") from exc

                if len(encoded) > 253 or not DOMAIN_REGEX.match(encoded):
                    raise TargetValidationError(f"Invalid domain '{trimmed}'")

            case TargetKind.URL:
                try:
                    parsed = urllib.parse.urlparse(trimmed)
                except Exception as exc:
                    raise TargetValidationError(f"Invalid URL '{trimmed}'") from exc

                if parsed.scheme.lower() not in ("http", "https"):
                    raise TargetValidationError("URL scheme must be http or https")

                if not parsed.netloc:
                    raise TargetValidationError("URL must include a valid host network location")

                host = parsed.hostname or ""
                if not self.allow_private and _is_private_ip(host):
                    raise TargetValidationError(
                        f"SSRF Protection: Target URL host '{host}' is in a private network range"
                    )

            case TargetKind.IP:
                try:
                    ip = ipaddress.ip_address(trimmed)
                except ValueError as exc:
                    raise TargetValidationError(f"Invalid IP address '{trimmed}'") from exc

                if not self.allow_private and (
                    ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                ):
                    raise TargetValidationError(
                        f"SSRF Protection: Target IP '{trimmed}' is in a private network range"
                    )

            case TargetKind.ORGANIZATION:
                if len(trimmed) < 2 or len(trimmed) > 120:
                    raise TargetValidationError(
                        "Organization name must be between 2 and 120 characters"
                    )

            case TargetKind.PHONE:
                try:
                    import phonenumbers

                    # Parse with best effort
                    parsed = phonenumbers.parse(trimmed, None if trimmed.startswith("+") else "US")
                    if not phonenumbers.is_possible_number(parsed):
                        raise TargetValidationError(f"Invalid phone number '{trimmed}'")
                except TargetValidationError:
                    raise
                except Exception as exc:
                    # Fallback regex if library parsing error
                    phone_clean = re.sub(r"[\s\-\(\)\.]", "", trimmed)
                    if not re.match(r"^\+?[0-9]{7,15}$", phone_clean):
                        raise TargetValidationError(f"Invalid phone number '{trimmed}'") from exc

            case TargetKind.NATIONAL_ID:
                # Reject dangerous characters
                clean_id = re.sub(r"[\s\-\./]", "", trimmed)
                if len(clean_id) < 4 or len(clean_id) > 40:
                    raise TargetValidationError(
                        f"National ID/Tax identifier '{trimmed}' length must be between 4 and 40 characters"
                    )
                if not re.match(r"^[a-zA-Z0-9\-\.\s/]{4,40}$", trimmed):
                    raise TargetValidationError(
                        f"National ID '{trimmed}' contains invalid characters"
                    )

            case TargetKind.REPOSITORY:
                if not (
                    trimmed.startswith("http://")
                    or trimmed.startswith("https://")
                    or trimmed.startswith("git@")
                    or re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", trimmed)
                ):
                    raise TargetValidationError(
                        f"Invalid repository reference '{trimmed}'. Must be a URL or 'owner/repo'"
                    )

            case TargetKind.PERSON_NAME:
                if len(trimmed) < 2 or len(trimmed) > 100:
                    raise TargetValidationError(
                        "Person name must be between 2 and 100 characters"
                    )
                if re.search(r"[;|<>&`$]", trimmed):
                    raise TargetValidationError(
                        f"Person name '{trimmed}' contains invalid characters"
                    )

            case TargetKind.LOCATION:
                if len(trimmed) < 2 or len(trimmed) > 120:
                    raise TargetValidationError(
                        "Location must be between 2 and 120 characters"
                    )
                if re.search(r"[;|<>&`$]", trimmed):
                    raise TargetValidationError(
                        f"Location '{trimmed}' contains invalid characters"
                    )


@dataclass(frozen=True, slots=True)
class InvestigationSettings:
    store_raw: bool = False
    timeout_ms: int = 30_000
    max_results_per_adapter: int = 500
    depth: int = 1
    concurrency: int = 2
    selected_engines: tuple[str, ...] = ()
    allow_private_targets: bool = False


@dataclass(frozen=True, slots=True)
class UserId:
    value: UUID
