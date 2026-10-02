import time

from src.app.infrastructure.logging import logger


def warmup_subsystems() -> dict[str, float]:
    """
    Pre-warms static data tables, country ID plugins, and heavy module imports.
    Eliminates the 11.6-second cold-import stall during runtime investigations.
    """
    start = time.monotonic()

    # 1. Warm phonenumbers carrier & geocoder static data tables
    try:
        import phonenumbers
        from phonenumbers import carrier, geocoder

        sample_num = phonenumbers.parse("+12025550143", "US")
        _ = carrier.name_for_number(sample_num, "en")
        _ = geocoder.description_for_number(sample_num, "en")
    except Exception as exc:
        logger.debug("Warmup: phonenumbers pre-warm skipped", error=str(exc))

    # 2. Warm stdnum and idnumbers plugins
    try:
        import idnumbers  # noqa: F401
        import stdnum  # noqa: F401
    except Exception as exc:
        logger.debug("Warmup: id validation pre-warm skipped", error=str(exc))

    # 3. Warm dynamic adapter registry
    try:
        from src.adapters.registry import registry

        _ = registry.list_all()
    except Exception as exc:
        logger.debug("Warmup: adapter registry pre-warm skipped", error=str(exc))

    duration_ms = (time.monotonic() - start) * 1000.0
    logger.info("OpenIntel subsystems pre-warmed successfully", duration_ms=round(duration_ms, 2))
    return {"warmup_duration_ms": duration_ms}
