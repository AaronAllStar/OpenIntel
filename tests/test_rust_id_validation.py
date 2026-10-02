import asyncio
import time
from uuid import uuid4

import openintel_core
import pytest

from src.adapters.id_validation.adapter import IdValidationAdapter
from src.app.domain.enums import EntityKind, TargetKind
from src.app.domain.ports.adapter import AdapterInput, EntityEvent
from src.app.domain.value_objects import Target


def test_openintel_core_engine_info():
    info = openintel_core.postgres_engine_info()
    assert "OpenIntel Rust Engine" in info
    assert "PostgreSQL" in info


def test_openintel_core_single_validation():
    # Valid Spain DNI
    es_res = openintel_core.validate_national_id("12345678Z")
    assert len(es_res) == 1
    assert es_res[0]["scheme"] == "Spain DNI"
    assert es_res[0]["country"] == "ESP"

    # Valid Brazil CPF
    br_res = openintel_core.validate_national_id("11144477735")
    assert len(br_res) == 1
    assert br_res[0]["scheme"] == "Brazil CPF"
    assert br_res[0]["country"] == "BRA"

    # Invalid ID
    invalid_res = openintel_core.validate_national_id("INVALID_TEST_999")
    assert len(invalid_res) == 0


def test_openintel_core_batch_validation():
    ids = ["12345678Z", "11144477735", "INVALID_XYZ"]
    batch_results = openintel_core.validate_batch(ids)
    assert len(batch_results) == 3
    assert len(batch_results[0]) == 1
    assert batch_results[0][0]["scheme"] == "Spain DNI"
    assert len(batch_results[1]) == 1
    assert batch_results[1][0]["scheme"] == "Brazil CPF"
    assert len(batch_results[2]) == 0


@pytest.mark.asyncio
async def test_id_validation_adapter_with_rust():
    adapter = IdValidationAdapter()
    input_data = AdapterInput(
        investigation_id=uuid4(),
        target=Target(kind=TargetKind.NATIONAL_ID, value="12345678Z"),
    )
    cancel_token = asyncio.Event()

    events = []
    async for event in adapter.run(input_data, cancel_token):
        events.append(event)

    entity_events = [e for e in events if isinstance(e, EntityEvent)]
    assert len(entity_events) >= 1
    validated = entity_events[0].entity
    assert validated.kind == EntityKind.NATIONAL_ID
    assert validated.value == "ESP:12345678Z"
    assert validated.attributes["checksum_verified"] is True
    assert validated.attributes["scheme"] == "Spain DNI"


@pytest.mark.asyncio
async def test_id_validation_adapter_fallback(monkeypatch):
    # Disable Rust validator via settings monkeypatch to test Python fallback path
    from src.app.infrastructure import config

    class MockSettings:
        USE_RUST_ID_VALIDATOR = False

    monkeypatch.setattr(config, "get_settings", lambda: MockSettings())

    adapter = IdValidationAdapter()
    input_data = AdapterInput(
        investigation_id=uuid4(),
        target=Target(kind=TargetKind.NATIONAL_ID, value="12345678Z"),
    )
    cancel_token = asyncio.Event()

    events = []
    async for event in adapter.run(input_data, cancel_token):
        events.append(event)

    entity_events = [e for e in events if isinstance(e, EntityEvent)]
    assert len(entity_events) >= 1
    validated = entity_events[0].entity
    assert validated.kind == EntityKind.NATIONAL_ID
    assert "ESP" in validated.value


def test_id_validation_benchmark_target_speedup():
    """
    Benchmark target: Assert Rust validator achieves >= 5x speedup over pure Python.
    """
    import stdnum.br.cpf as br_cpf
    import stdnum.es.dni as es_dni
    import stdnum.es.nie as es_nie
    import stdnum.fr.nif as fr_nif
    import stdnum.it.codicefiscale as it_cf
    import stdnum.mx.curp as mx_curp
    import stdnum.us.ssn as us_ssn

    python_schemes = [es_dni, es_nie, br_cpf, us_ssn, mx_curp, fr_nif, it_cf]
    test_ids = ["12345678Z", "11144477735", "INVALID12345", "X1234567L"] * 100

    # 1. Pure Python baseline (iterating across scheme validators)
    start_py = time.perf_counter()
    for raw in test_ids:
        for mod in python_schemes:
            try:
                mod.is_valid(raw)
            except Exception:
                pass
    py_duration = time.perf_counter() - start_py

    # 2. Rust execution via PyO3
    start_rust = time.perf_counter()
    for raw in test_ids:
        _ = openintel_core.validate_national_id(raw)
    rust_duration = time.perf_counter() - start_rust

    speedup = py_duration / max(rust_duration, 1e-9)
    print(
        f"\n[BENCHMARK] Python: {py_duration * 1000:.2f}ms, Rust: {rust_duration * 1000:.2f}ms -> Speedup: {speedup:.2f}x"
    )

    assert speedup >= 5.0, f"Expected speedup >= 5.0x, but got {speedup:.2f}x"
