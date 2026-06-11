# system-design-distributed-id-generator

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

## Throughput math

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
