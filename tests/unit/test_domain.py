from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.app.domain.entities import Investigation
from src.app.domain.enums import InvestigationStatus, InvestigationType, TargetKind
from src.app.domain.errors import InvalidStateTransitionError, TargetValidationError
from src.app.domain.value_objects import InvestigationSettings, Target, UserId


def test_target_validation_valid():
    t1 = Target(kind=TargetKind.USERNAME, value="osint_analyst_01")
    assert t1.value == "osint_analyst_01"

    t2 = Target(kind=TargetKind.EMAIL, value="investigator@example.com")
    assert t2.value == "investigator@example.com"

    t3 = Target(kind=TargetKind.DOMAIN, value="target.org")
    assert t3.value == "target.org"

    t4 = Target(kind=TargetKind.URL, value="https://target.org/profiles")
    assert t4.value == "https://target.org/profiles"

    t5 = Target(kind=TargetKind.IP, value="8.8.8.8")
    assert t5.value == "8.8.8.8"

    t6 = Target(kind=TargetKind.PHONE, value="+1 202-555-0143")
    assert t6.value == "+1 202-555-0143"


def test_target_validation_phone():
    # Valid formats
    t = Target(kind=TargetKind.PHONE, value="+44 20 7946 0991")
    assert t.value == "+44 20 7946 0991"

    # Invalid phone format
    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.PHONE, value="abc123notaphone")


def test_target_validation_national_id():
    t = Target(kind=TargetKind.NATIONAL_ID, value="12345678Z")
    assert t.value == "12345678Z"

    # Too short
    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.NATIONAL_ID, value="12")

    # Dangerous characters
    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.NATIONAL_ID, value="123456; rm -rf")


def test_target_validation_repository():
    t1 = Target(kind=TargetKind.REPOSITORY, value="octocat/Hello-World")
    assert t1.value == "octocat/Hello-World"

    t2 = Target(kind=TargetKind.REPOSITORY, value="https://github.com/torvalds/linux")
    assert t2.value == "https://github.com/torvalds/linux"

    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.REPOSITORY, value="repo; echo bad")


def test_target_validation_person_name():
    t = Target(kind=TargetKind.PERSON_NAME, value="Carlos Navarro")
    assert t.value == "Carlos Navarro"

    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.PERSON_NAME, value="C")

    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.PERSON_NAME, value="Carlos; rm -rf")


def test_target_validation_location():
    t = Target(kind=TargetKind.LOCATION, value="Madrid, Spain")
    assert t.value == "Madrid, Spain"

    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.LOCATION, value="M")

    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.LOCATION, value="Madrid; echo bad")


def test_target_validation_invalid_username():
    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.USERNAME, value="user; rm -rf /")

    with pytest.raises(TargetValidationError):
        Target(kind=TargetKind.USERNAME, value="user name with spaces")


def test_target_validation_ssrf():
    # Private IP rejected by default
    with pytest.raises(TargetValidationError, match="SSRF Protection"):
        Target(kind=TargetKind.IP, value="192.168.1.1", allow_private=False)

    with pytest.raises(TargetValidationError, match="SSRF Protection"):
        Target(kind=TargetKind.IP, value="127.0.0.1", allow_private=False)

    with pytest.raises(TargetValidationError, match="SSRF Protection"):
        Target(kind=TargetKind.URL, value="http://10.0.0.1/admin", allow_private=False)

    # Allowed when explicitly specified
    t = Target(kind=TargetKind.IP, value="127.0.0.1", allow_private=True)
    assert t.value == "127.0.0.1"


def test_investigation_lifecycle_transitions():
    inv = Investigation(
        id=uuid4(),
        name="Test Case",
        target=Target(kind=TargetKind.USERNAME, value="target_user"),
        type=InvestigationType.QUICK,
        status=InvestigationStatus.PENDING,
        created_at=datetime.now(UTC),
        started_at=None,
        finished_at=None,
        created_by=UserId(uuid4()),
        settings=InvestigationSettings(),
    )

    assert inv.status == InvestigationStatus.PENDING

    inv.transition_to(InvestigationStatus.RUNNING)
    assert inv.status == InvestigationStatus.RUNNING
    assert inv.started_at is not None

    inv.transition_to(InvestigationStatus.WORKING)
    assert inv.status == InvestigationStatus.WORKING

    inv.transition_to(InvestigationStatus.REVIEW)
    assert inv.status == InvestigationStatus.REVIEW
    assert inv.finished_at is not None

    inv.transition_to(InvestigationStatus.FINAL)
    assert inv.status == InvestigationStatus.FINAL

    # Cannot transition from FINAL
    with pytest.raises(InvalidStateTransitionError):
        inv.transition_to(InvestigationStatus.RUNNING)
