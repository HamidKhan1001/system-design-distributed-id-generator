# system-design-distributed-id-generator

[![CI](https://github.com/HamidKhan1001/system-design-distributed-id-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/HamidKhan1001/system-design-distributed-id-generator/actions/workflows/ci.yml)

Snowflake-style globally unique 64-bit ID generator — ordered, collision-free across multiple data centers without a centralized database.

## Bit layout (63 usable bits)

```
 63                                    22        17       12         0
  ┌────────────────────────────────────┬─────────┬────────┬──────────┐
  │       timestamp (41 bits)          │ DC (5b) │ W (5b) │ seq (12b)│
  └────────────────────────────────────┴─────────┴────────┴──────────┘
```

| Field        | Bits | Max value | Purpose                           |
|-------------|------|-----------|-----------------------------------|
| Timestamp   | 41   | ~69 years | ms since custom epoch             |
| Datacenter  | 5    | 31        | up to 32 datacenters              |
| Worker      | 5    | 31        | up to 32 workers per datacenter   |
| Sequence    | 12   | 4095      | IDs within the same millisecond   |

## Capacity math (theoretical maximum, not measured)

- **4,096 IDs/ms** per worker (sequence rolls over every ms)
- **1,024 workers** max (32 DCs × 32 workers each)
- **4,194,304 IDs/ms** globally across all workers

## Usage

```python
from idgen import SnowflakeGenerator, NodeConfig

gen = SnowflakeGenerator(NodeConfig(datacenter_id=1, worker_id=3))
sid = gen.next_id()       # 64-bit int, monotonically increasing
gen.parse(sid)            # → {timestamp_ms, datacenter_id, worker_id, sequence}
SnowflakeGenerator.max_ids_per_ms(1024)  # → 4_194_304
```

## Race condition safety

`threading.Lock` ensures the sequence counter and last-ms timestamp are updated atomically within a single process. Across nodes, uniqueness is guaranteed by the datacenter+worker ID bits.

## Running tests

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v   # 20 tests
```

## Tradeoffs and limitations

- **Single process.** Uniqueness across processes depends on each one being configured with a distinct datacenter and worker ID. Nothing here assigns or checks those IDs, which in practice needs a coordination service or deployment config.
- **Clock regression raises.** If the system clock moves backwards, `next_id` raises `ClockBackwardError` instead of risking a duplicate. A production service would typically wait out small regressions.
- **The throughput figures above are arithmetic from the bit layout**, not a benchmark. Python and the lock cap real per-process throughput far below 4,096 IDs per millisecond.
- **Wall-clock timestamps.** IDs are time-ordered only to millisecond precision and only as far as the clock is accurate.
