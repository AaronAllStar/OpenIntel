import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.adapters.base import BaseSubprocessAdapter
from src.adapters.sherlock.adapter import SherlockAdapter
from src.app.domain.enums import TargetKind
from src.app.domain.ports.adapter import AdapterInput, AdapterOptions
from src.app.domain.value_objects import Target


@pytest.mark.asyncio
async def test_subprocess_never_uses_shell():
    """Verify that BaseSubprocessAdapter passes arguments as a list without shell expansion."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"output", b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        malicious_input = "malicious_user; rm -rf /"
        args = ["sherlock", malicious_input]

        await BaseSubprocessAdapter.run_subprocess_safely(args, timeout_seconds=5.0)

        # Assert create_subprocess_exec was called with separate positional arguments, NOT shell=True
        mock_exec.assert_called_once_with(
            "sherlock",
            malicious_input,
            stdout=-1,  # subprocess.PIPE
            stderr=-1,  # subprocess.PIPE
        )


@pytest.mark.asyncio
async def test_sherlock_adapter_yields_events():
    target = Target(kind=TargetKind.USERNAME, value="test_user")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = SherlockAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    # Must yield at least one ProgressEvent and one EntityEvent
    has_progress = any(e.__class__.__name__ == "ProgressEvent" for e in events)
    has_entity = any(e.__class__.__name__ == "EntityEvent" for e in events)
    assert has_progress
    assert has_entity


@pytest.mark.asyncio
async def test_phoneinfoga_adapter_and_classification():
    from src.adapters.phoneinfoga.adapter import PhoneInfogaAdapter
    from src.app.domain.enums import InfoClassification

    target = Target(kind=TargetKind.PHONE, value="+1 202-555-0143")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = PhoneInfogaAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    entity_events = [e for e in events if e.__class__.__name__ == "EntityEvent"]
    assert len(entity_events) > 0
    first_evidence = entity_events[0].evidence
    assert first_evidence.info_classification == InfoClassification.PUBLIC_REGISTRY


@pytest.mark.asyncio
async def test_amass_adapter_yields_events():
    from src.adapters.amass.adapter import AmassAdapter

    target = Target(kind=TargetKind.DOMAIN, value="target.org")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = AmassAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    has_entity = any(e.__class__.__name__ == "EntityEvent" for e in events)
    assert has_entity


@pytest.mark.asyncio
async def test_id_validation_adapter():
    from src.adapters.id_validation.adapter import IdValidationAdapter
    from src.app.domain.enums import InfoClassification

    target = Target(kind=TargetKind.NATIONAL_ID, value="12345678Z")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = IdValidationAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    entity_events = [e for e in events if e.__class__.__name__ == "EntityEvent"]
    assert len(entity_events) > 0
    assert entity_events[0].evidence.info_classification == InfoClassification.PUBLIC_REGISTRY


@pytest.mark.asyncio
async def test_octosuite_adapter():
    from src.adapters.octosuite.adapter import OctoSuiteAdapter

    target = Target(kind=TargetKind.REPOSITORY, value="openintel/scanner")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = OctoSuiteAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_dnstwist_adapter():
    from src.adapters.dnstwist.adapter import DNSTwistAdapter

    target = Target(kind=TargetKind.DOMAIN, value="target.org")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = DNSTwistAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_blackbird_adapter():
    from src.adapters.blackbird.adapter import BlackbirdAdapter

    target = Target(kind=TargetKind.USERNAME, value="osint_tester")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = BlackbirdAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_trufflehog_adapter():
    from src.adapters.trufflehog.adapter import TruffleHogAdapter

    target = Target(kind=TargetKind.REPOSITORY, value="torvalds/linux")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = TruffleHogAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_twikit_adapter():
    from src.adapters.twikit.adapter import TwikitAdapter

    target = Target(kind=TargetKind.USERNAME, value="osint_analyst")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = TwikitAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_instaloader_adapter():
    from src.adapters.instaloader.adapter import InstaloaderAdapter

    target = Target(kind=TargetKind.USERNAME, value="osint_analyst")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = InstaloaderAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_whatsapp_adapter():
    from src.adapters.whatsapp.adapter import WhatsAppAdapter

    target = Target(kind=TargetKind.PHONE, value="+34 612 345 678")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = WhatsAppAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_email_enrich_adapter():
    from src.adapters.email_enrich.adapter import EmailEnrichAdapter

    target = Target(kind=TargetKind.PERSON_NAME, value="Carlos Navarro")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = EmailEnrichAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)


@pytest.mark.asyncio
async def test_email_finder_adapter():
    from src.adapters.email_finder.adapter import EmailFinderAdapter

    target = Target(kind=TargetKind.DOMAIN, value="target.org")
    adapter_input = AdapterInput(
        target=target,
        investigation_id=uuid4(),
        options=AdapterOptions(),
    )
    adapter = EmailFinderAdapter()
    cancel = asyncio.Event()

    events = []
    async for event in adapter.run(adapter_input, cancel):
        events.append(event)

    assert len(events) > 0
    assert any(e.__class__.__name__ == "EntityEvent" for e in events)
