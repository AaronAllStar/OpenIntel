import importlib.metadata
from collections.abc import Sequence

from src.app.domain.enums import TargetKind
from src.app.domain.ports.adapter import HealthStatus, OsintAdapter
from src.app.infrastructure.logging import logger


class AdapterRegistry:
    """
    Dynamic registry for OpenIntel OSINT adapters.
    Supports registration via Python entry points ('openintel.adapters')
    or explicit registration, decoupling engine discovery from the core runner.
    """

    def __init__(self) -> None:
        self._adapters: dict[str, OsintAdapter] = {}
        self._initialized: bool = False

    def register(self, adapter: OsintAdapter | type[OsintAdapter]) -> None:
        """Registers an adapter instance or class."""
        instance = adapter() if isinstance(adapter, type) else adapter
        self._adapters[instance.name] = instance
        logger.debug("Registered OSINT adapter", adapter=instance.name, version=instance.version)

    def get(self, name: str) -> OsintAdapter | None:
        self._ensure_initialized()
        return self._adapters.get(name)

    def list_all(self) -> list[OsintAdapter]:
        self._ensure_initialized()
        return list(self._adapters.values())

    def get_for_target(
        self,
        target_kind: TargetKind,
        selected_engines: Sequence[str] | None = None,
    ) -> list[OsintAdapter]:
        """
        Resolves applicable adapters for a given TargetKind, with optional user overrides.
        """
        self._ensure_initialized()
        all_adapters = list(self._adapters.values())

        if selected_engines and len(selected_engines) > 0:
            selected_set = {e.lower().replace("-", "_") for e in selected_engines}
            return [
                a for a in all_adapters
                if a.name in selected_set and target_kind in a.supported_targets
            ]

        # Filter by supported target kinds
        return [a for a in all_adapters if target_kind in a.supported_targets]

    def health_check_all(self) -> dict[str, HealthStatus]:
        """Runs health checks on all registered adapters."""
        self._ensure_initialized()
        return {name: adapter.health_check() for name, adapter in self._adapters.items()}

    def load_entry_points(self, group: str = "openintel.adapters") -> int:
        """Loads third-party and plugin adapters exposed via Python entry points."""
        count = 0
        try:
            entry_points = importlib.metadata.entry_points(group=group)
            for ep in entry_points:
                try:
                    adapter_cls = ep.load()
                    self.register(adapter_cls)
                    count += 1
                except Exception as exc:
                    logger.error("Failed to load adapter entry point", entry_point=ep.name, error=str(exc))
        except Exception as exc:
            logger.debug("Error checking entry points", error=str(exc))
        return count

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self._register_builtin_adapters()
            self.load_entry_points()
            self._initialized = True

    def _register_builtin_adapters(self) -> None:
        """Loads all 27 built-in OSINT adapters."""
        from src.adapters.amass.adapter import AmassAdapter
        from src.adapters.bellingcat.adapter import BellingcatTelegramAdapter
        from src.adapters.blackbird.adapter import BlackbirdAdapter
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

        builtin = [
            SherlockAdapter,
            MaigretAdapter,
            TheHarvesterAdapter,
            SpiderFootAdapter,
            PhotonAdapter,
            ReconNgAdapter,
            AmassAdapter,
            PhoneInfogaAdapter,
            MetagoofilAdapter,
            BlackbirdAdapter,
            SocialscanAdapter,
            OctoSuiteAdapter,
            TwikitAdapter,
            InstaloaderAdapter,
            HoleheAdapter,
            GHuntAdapter,
            H8mailAdapter,
            EmailEnrichAdapter,
            EmailFinderAdapter,
            BellingcatTelegramAdapter,
            IgnorantAdapter,
            SearchPhoneAdapter,
            WhatsAppAdapter,
            DNSTwistAdapter,
            CrossLinkedAdapter,
            TruffleHogAdapter,
            IdValidationAdapter,
        ]

        for adapter_cls in builtin:
            self.register(adapter_cls)


_global_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    return _global_registry
