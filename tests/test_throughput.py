import time
from idgen import SnowflakeGenerator, NodeConfig, IDS_PER_MS
from idgen.snowflake import MAX_DATACENTER, MAX_WORKER, TIMESTAMP_BITS, DATACENTER_BITS, WORKER_BITS, SEQUENCE_BITS


def test_ids_per_ms_constant():
    assert IDS_PER_MS == 4096


def test_max_ids_single_worker():
    assert SnowflakeGenerator.max_ids_per_ms(1) == 4096


def test_max_ids_all_workers():
    assert SnowflakeGenerator.max_ids_per_ms(32) == 4096 * 32


def test_datacenter_worker_capacity():
    max_workers = (MAX_DATACENTER + 1) * (MAX_WORKER + 1)
    assert max_workers == 1024
    assert SnowflakeGenerator.max_ids_per_ms(max_workers) == 4096 * 1024


def test_generates_fast():
    g = SnowflakeGenerator(NodeConfig(datacenter_id=0, worker_id=0))
    start = time.perf_counter()
    for _ in range(10_000):
        g.next_id()
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0


def test_bit_layout_sums_to_63():
    total = TIMESTAMP_BITS + DATACENTER_BITS + WORKER_BITS + SEQUENCE_BITS
    assert total == 63


def test_epoch_makes_ids_fit_63_bits():
    g = SnowflakeGenerator(NodeConfig(datacenter_id=0, worker_id=0, epoch_ms=1_700_000_000_000))
    sid = g.next_id()
    assert sid < (1 << 63)


def test_different_datacenters_no_collision():
    g1 = SnowflakeGenerator(NodeConfig(datacenter_id=0, worker_id=0))
    g2 = SnowflakeGenerator(NodeConfig(datacenter_id=1, worker_id=0))
    ids1 = {g1.next_id() for _ in range(500)}
    ids2 = {g2.next_id() for _ in range(500)}
    assert ids1.isdisjoint(ids2)
