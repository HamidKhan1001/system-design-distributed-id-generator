import threading
import pytest
from idgen import SnowflakeGenerator, NodeConfig, ClockBackwardError
from idgen.snowflake import MAX_DATACENTER, MAX_WORKER


def test_generates_positive_id(gen):
    assert gen.next_id() > 0


def test_ids_are_increasing(gen):
    ids = [gen.next_id() for _ in range(100)]
    assert ids == sorted(ids)


def test_ids_unique(gen):
    ids = [gen.next_id() for _ in range(1000)]
    assert len(set(ids)) == 1000


def test_parse_round_trip(gen):
    sid = gen.next_id()
    p = gen.parse(sid)
    assert p["datacenter_id"] == 1
    assert p["worker_id"] == 1
    assert p["sequence"] >= 0
    assert p["timestamp_ms"] > 0


def test_different_workers_no_collision():
    g1 = SnowflakeGenerator(NodeConfig(datacenter_id=0, worker_id=0))
    g2 = SnowflakeGenerator(NodeConfig(datacenter_id=0, worker_id=1))
    ids1 = {g1.next_id() for _ in range(500)}
    ids2 = {g2.next_id() for _ in range(500)}
    assert ids1.isdisjoint(ids2)


def test_invalid_datacenter_id():
    with pytest.raises(ValueError):
        NodeConfig(datacenter_id=32, worker_id=0)


def test_invalid_worker_id():
    with pytest.raises(ValueError):
        NodeConfig(datacenter_id=0, worker_id=32)


def test_max_datacenter():
    g = SnowflakeGenerator(NodeConfig(datacenter_id=MAX_DATACENTER, worker_id=MAX_WORKER))
    assert g.next_id() > 0


def test_clock_backward_raises():
    g = SnowflakeGenerator(NodeConfig(datacenter_id=0, worker_id=0))
    g._last_ms = int(1e13)  # far future
    with pytest.raises(ClockBackwardError):
        g.next_id()


def test_thread_safety():
    g = SnowflakeGenerator(NodeConfig(datacenter_id=0, worker_id=0))
    results = []
    lock = threading.Lock()

    def worker():
        for _ in range(200):
            sid = g.next_id()
            with lock:
                results.append(sid)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 1000
    assert len(set(results)) == 1000


def test_64_bit_id(gen):
    sid = gen.next_id()
    assert sid.bit_length() <= 63


def test_parse_sequence_in_range(gen):
    ids = [gen.next_id() for _ in range(10)]
    parsed = [gen.parse(i) for i in ids]
    assert all(0 <= p["sequence"] <= 4095 for p in parsed)
