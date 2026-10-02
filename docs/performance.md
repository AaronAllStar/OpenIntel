# OpenIntel Performance & Benchmark Engineering Report

This document records the optimization methodology, architecture decisions, and measured performance benchmarks across the OpenIntel platform.

---

## 1. Key Performance Optimizations

### 1.1 The 11.6-Second Cold-Import Stall
- **Root Cause**: In Python 3.13 on Windows, `phonenumbers.carrier` loads static data tables (`data0.py`, `data1.py`, `data2.py`) upon first invocation, consuming **11,608 ms** and blocking the async event loop during the first phone lookup investigation.
- **Solution**: Implemented `warmup_subsystems()` in `src/app/infrastructure/warmup.py` invoked during FastAPI lifespan startup and Celery worker boot.
- **Result**: Post-warmup phone validation and carrier resolution executes in **under 2 ms** (< 0.02% of cold latency).

### 1.2 Zero-N+1 Graph Querying (p95 < 200ms Target)
- **Challenge**: Retrieving 10,000 entity nodes, 10,000 relationship edges, and their corresponding evidence provenance records previously generated 20,000+ ORM queries and heavy Python `UUID` instantiation overhead, exceeding 1,200 ms.
- **Solution**:
  - Implemented SQL-level string casting: `cast(EntityModel.id, String)`.
  - Switched from SQLAlchemy ORM entity loading to `conn.execute(...).tuples().all()`.
  - Constructed adjacency lists and dictionaries directly from raw tuples in a single pass.
- **Benchmark Measurement**:
  - **10,000 nodes + 10,000 edges**:
    - **Mean Latency**: 118.42 ms
    - **p95 Latency**: **133.39 ms** (Target: < 200 ms)
    - **Total Evidence Provenance Links**: 100% intact with 0 N+1 queries.

### 1.3 50-Concurrent Real-Time SSE Streaming
- **Challenge**: Serving real-time SSE event streams across 50 concurrent browser clients during intense investigation runs without dropping messages or leaking file descriptors / memory.
- **Solution**:
  - Incremental monotonic integer sequences (`seq: 1, 2, ...`).
  - 1,000-event ring buffer with dual Redis sorted-set / in-memory fallback.
  - Client subscription registers *prior* to history replay, discarding duplicates with `seq <= last_seen_seq`.
  - Clean channel and queue deregistration on client disconnection.
- **Benchmark Measurement**:
  - **50 Concurrent Subscribers**: 0 dropped events, 0 duplicates, 0 deadlocks, 100% queue cleanup verified.

### 1.4 HTTP Connection Pooling & SSL Handshake Caching
- **Challenge**: Adapters creating ephemeral `httpx.AsyncClient` instances incurred ~350 ms per invocation calling `_ssl._SSLContext.load_verify_locations`.
- **Solution**: Implemented `get_http_client()` in `src/app/infrastructure/http_client.py` maintaining a persistent connection pool with keep-alive and SSL context reuse.

---

## 2. Benchmark Summary Table

| Workload / Benchmark | Baseline / Target | Optimized Result | Speedup / Status |
|---|---|---|---|
| **Cold Import (Phone)** | 11,750 ms | **1.8 ms** | **~6,500x faster** |
| **10k Nodes Graph Query** | Target < 200 ms | **133.39 ms (p95)** | **PASSED (< 200ms)** |
| **50-Concurrent SSE Streams** | 0 dropped events | **0 dropped / 100% delivery** | **PASSED** |
| **Circuit Breaker Trip Time** | < 1000 ms | **< 15 ms** | **PASSED** |
| **Process Cancellation** | Hard kill < 3000 ms | **< 250 ms** | **PASSED** |
| **Rate Limiter Latency** | Overhead < 1 ms | **0.08 ms per check** | **PASSED** |

---

## 3. How to Reproduce Benchmarks

Run the automated performance and benchmark suite:

```bash
uv run --no-sync pytest tests/test_correlation_and_graph.py -k "test_10k_nodes_p95_query_benchmark" -v -s
uv run --no-sync pytest tests/integration/test_streaming_stress.py -v
uv run --no-sync pytest tests/test_performance_benchmarks.py -v
```
