import asyncio
import time
from collections.abc import AsyncIterator, Sequence

from src.adapters.amass.adapter import AmassAdapter
from src.adapters.bellingcat.adapter import BellingcatTelegramAdapter
from src.adapters.blackbird.adapter import BlackbirdAdapter
from src.adapters.circuit_breaker import get_circuit_breaker
from src.adapters.crosslinked.adapter import CrossLinkedAdapter
from src.adapters.dnstwist.adapter import DNSTwistAdapter
from src.adapters.email_enrich.adapter import EmailEnrichAdapter
from src.adapters.email_finder.adapter import EmailFinderAdapter
from src.adapters.ghunt.adapter import GHuntAdapter
from src.adapters.h8mail.adapter import H8mailAdapter
from src.adapters.holehe.adapter import HoleheAdapter
from src.adapters.id_validation.adapter import IdValidationAdapter
from src.adapters.ignorant.adapter import IgnorantAdapter
from src.adapters.instaloader.adapter import InstaloaderAdapter
from src.adapters.maigret.adapter import MaigretAdapter
from src.adapters.metagoofil.adapter import MetagoofilAdapter
from src.adapters.octosuite.adapter import OctoSuiteAdapter
from src.adapters.phoneinfoga.adapter import PhoneInfogaAdapter
from src.adapters.photon.adapter import PhotonAdapter
from src.adapters.recon_ng.adapter import ReconNgAdapter
from src.adapters.searchphone.adapter import SearchPhoneAdapter
from src.adapters.sherlock.adapter import SherlockAdapter
from src.adapters.socialscan.adapter import SocialscanAdapter
from src.adapters.spiderfoot.adapter import SpiderFootAdapter
from src.adapters.the_harvester.adapter import TheHarvesterAdapter
from src.adapters.trufflehog.adapter import TruffleHogAdapter
from src.adapters.twikit.adapter import TwikitAdapter
from src.adapters.whatsapp.adapter import WhatsAppAdapter
from src.app.domain.enums import TargetKind
from src.app.domain.ports.adapter import (
    AdapterEvent,
    AdapterInput,
    EngineStatusEvent,
    LogEvent,
    OsintAdapter,
)

ALL_ADAPTERS: tuple[OsintAdapter, ...] = (
    # Core & discovery engines
    SherlockAdapter(),
    MaigretAdapter(),
    TheHarvesterAdapter(),
    SpiderFootAdapter(),
    PhotonAdapter(),
    ReconNgAdapter(),
    AmassAdapter(),
    PhoneInfogaAdapter(),
    MetagoofilAdapter(),
    # Extended username, profile & repository intelligence
    BlackbirdAdapter(),
    SocialscanAdapter(),
    OctoSuiteAdapter(),
    TwikitAdapter(),
    InstaloaderAdapter(),
    # Extended email & identity signal adapters
    HoleheAdapter(),
    GHuntAdapter(),
    H8mailAdapter(),
    EmailEnrichAdapter(),
    EmailFinderAdapter(),
    # Extended phone & telecom intelligence
    BellingcatTelegramAdapter(),
    IgnorantAdapter(),
    SearchPhoneAdapter(),
    WhatsAppAdapter(),
    # Network, domain & web intelligence
    DNSTwistAdapter(),
    CrossLinkedAdapter(),
    TruffleHogAdapter(),
    # Legal registry & national ID checksum validator
    IdValidationAdapter(),
)

# Automated orchestration table based on user specification:
# X: Sherlock, twikit, Socialscan
# IG: Sherlock + Instaloader + Socialscan
# WhatsApp: Phoneinfoga + phonenumbers + WhatsApp
# Business emails: email-enrich + theHarvester + email-finder
DEFAULT_ORCHESTRATION: dict[TargetKind, tuple[str, ...]] = {
    TargetKind.USERNAME: ("sherlock", "twikit", "instaloader", "socialscan", "maigret", "blackbird", "octosuite"),
    TargetKind.PERSON_NAME: ("crosslinked", "email_enrich", "email_finder", "twikit", "instaloader", "the_harvester", "metagoofil"),
    TargetKind.EMAIL: ("the_harvester", "email_enrich", "holehe", "socialscan", "ghunt", "h8mail", "spiderfoot"),
    TargetKind.PHONE: ("phoneinfoga", "whatsapp", "bellingcat_telegram", "ignorant", "searchphone"),
    TargetKind.DOMAIN: (
        "amass",
        "the_harvester",
        "email_finder",
        "email_enrich",
        "recon_ng",
        "dnstwist",
        "spiderfoot",
        "photon",
        "metagoofil",
        "crosslinked",
    ),
    TargetKind.URL: ("photon", "spiderfoot", "trufflehog"),
    TargetKind.IP: ("spiderfoot",),
    TargetKind.ORGANIZATION: ("crosslinked", "email_finder", "recon_ng", "the_harvester", "metagoofil", "octosuite"),
    TargetKind.LOCATION: ("recon_ng", "the_harvester", "spiderfoot"),
    TargetKind.NATIONAL_ID: ("id_validation",),
    TargetKind.REPOSITORY: ("octosuite", "trufflehog"),
}


def get_adapters_for_target(
    target_kind: TargetKind,
    selected_engines: Sequence[str] | None = None,
) -> list[OsintAdapter]:
    """
    Intelligently decides which tools are appropriate based on TargetKind
    or user-selected overrides.
    """
    if selected_engines and len(selected_engines) > 0:
        selected_set = {e.lower().replace("-", "_") for e in selected_engines}
        return [a for a in ALL_ADAPTERS if a.name in selected_set and target_kind in a.supported_targets]

    # Automated intelligent default orchestration
    recommended_engine_names = set(DEFAULT_ORCHESTRATION.get(target_kind, ()))
    applicable = [a for a in ALL_ADAPTERS if a.name in recommended_engine_names and target_kind in a.supported_targets]

    # If none found via default table, fallback to any matching supported target
    if not applicable:
        applicable = [a for a in ALL_ADAPTERS if target_kind in a.supported_targets]

    return applicable


async def execute_adapters(
    adapters: Sequence[OsintAdapter],
    adapter_input: AdapterInput,
    cancel_event: asyncio.Event,
    max_concurrency: int = 2,
) -> AsyncIterator[AdapterEvent]:
    """
    Executes multiple OSINT adapters concurrently with a concurrency semaphore
    and merges their event streams into a unified async generator.
    A failure or timeout in one tool does not terminate the remaining tools.
    Emits per-engine status events ('ok' | 'timeout' | 'error' | 'skipped' | 'cancelled').
    """
    if not adapters:
        yield LogEvent(
            level="warn",
            message=f"No matching OSINT adapters found for target kind '{adapter_input.target.kind}'",
        )
        return

    if cancel_event.is_set():
        yield LogEvent(level="info", message="Investigation execution cancelled prior to starting adapters")
        return

    circuit_breaker = get_circuit_breaker()
    timeout_sec = (adapter_input.options.timeout_ms or 30000) / 1000.0
    semaphore = asyncio.Semaphore(max_concurrency)
    queue: asyncio.Queue[AdapterEvent | None] = asyncio.Queue()
    active_tasks = len(adapters)

    async def _worker(adapter: OsintAdapter) -> None:
        nonlocal active_tasks
        start_time = time.perf_counter()

        # Check cancellation before starting
        if cancel_event.is_set():
            active_tasks -= 1
            await queue.put(EngineStatusEvent(
                engine=adapter.name,
                status="cancelled",
                duration_ms=0.0,
                error="Cancelled prior to execution",
            ))
            if active_tasks == 0:
                await queue.put(None)
            return

        # Check circuit breaker
        if not circuit_breaker.can_execute(adapter.name):
            active_tasks -= 1
            await queue.put(LogEvent(
                level="warn",
                message=f"Adapter '{adapter.name}' skipped: circuit breaker is open",
            ))
            await queue.put(EngineStatusEvent(
                engine=adapter.name,
                status="skipped",
                duration_ms=0.0,
                error="Circuit breaker is open",
            ))
            if active_tasks == 0:
                await queue.put(None)
            return

        status = "ok"
        error_msg: str | None = None

        try:
            async with semaphore:
                if cancel_event.is_set():
                    status = "cancelled"
                    error_msg = "Cancelled prior to acquiring semaphore"
                    return

                async def _stream_adapter() -> None:
                    async for event in adapter.run(adapter_input, cancel_event):
                        if cancel_event.is_set():
                            raise asyncio.CancelledError()
                        await queue.put(event)

                await asyncio.wait_for(_stream_adapter(), timeout=timeout_sec)
                circuit_breaker.record_success(adapter.name)

        except TimeoutError:
            status = "timeout"
            error_msg = f"Timed out after {timeout_sec:.1f}s"
            circuit_breaker.record_failure(adapter.name, error_msg)
            await queue.put(LogEvent(
                level="warn",
                message=f"Adapter '{adapter.name}' timed out after {timeout_sec:.1f}s",
            ))
        except asyncio.CancelledError:
            status = "cancelled"
            error_msg = "Cancelled by user"
            await queue.put(LogEvent(
                level="info",
                message=f"Adapter '{adapter.name}' execution cancelled",
            ))
        except Exception as exc:
            status = "error"
            error_msg = str(exc)
            circuit_breaker.record_failure(adapter.name, exc)
            await queue.put(LogEvent(
                level="warn",
                message=f"Adapter '{adapter.name}' encountered an issue: {exc}",
            ))
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            await queue.put(EngineStatusEvent(
                engine=adapter.name,
                status=status,
                duration_ms=round(elapsed_ms, 2),
                error=error_msg,
            ))
            active_tasks -= 1
            if active_tasks == 0:
                await queue.put(None)  # Sentinel to terminate consumer

    # Launch background worker tasks
    for adapter in adapters:
        asyncio.create_task(_worker(adapter))

    # Stream merged events to caller
    while True:
        event = await queue.get()
        if event is None:
            break
        yield event
