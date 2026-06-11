import threading
import time
from .node import NodeConfig
from .exceptions import ClockBackwardError

TIMESTAMP_BITS = 41
DATACENTER_BITS = 5
WORKER_BITS = 5
SEQUENCE_BITS = 12

MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1
MAX_DATACENTER = (1 << DATACENTER_BITS) - 1
MAX_WORKER = (1 << WORKER_BITS) - 1

WORKER_SHIFT = SEQUENCE_BITS
DATACENTER_SHIFT = SEQUENCE_BITS + WORKER_BITS
TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_BITS + DATACENTER_BITS

IDS_PER_MS = MAX_SEQUENCE + 1  # 4096 per worker per millisecond


class SnowflakeGenerator:
    def __init__(self, config: NodeConfig):
        self._config = config
        self._sequence = 0
        self._last_ms = -1
        self._lock = threading.Lock()

    def next_id(self) -> int:
        with self._lock:
            now = self._current_ms()
            if now < self._last_ms:
                raise ClockBackwardError(
                    f"Clock moved backward by {self._last_ms - now} ms"
                )
            if now == self._last_ms:
                self._sequence = (self._sequence + 1) & MAX_SEQUENCE
                if self._sequence == 0:
                    now = self._wait_next_ms(self._last_ms)
            else:
                self._sequence = 0
            self._last_ms = now
            return self._compose(now, self._sequence)

    def parse(self, snowflake_id: int) -> dict:
        ts_ms = (snowflake_id >> TIMESTAMP_SHIFT) + self._config.epoch_ms
        datacenter = (snowflake_id >> DATACENTER_SHIFT) & MAX_DATACENTER
        worker = (snowflake_id >> WORKER_SHIFT) & MAX_WORKER
        seq = snowflake_id & MAX_SEQUENCE
        return {
            "timestamp_ms": ts_ms,
            "datacenter_id": datacenter,
            "worker_id": worker,
            "sequence": seq,
        }

    @staticmethod
    def max_ids_per_ms(worker_count: int = 1) -> int:
        return IDS_PER_MS * worker_count

    def _compose(self, now_ms: int, seq: int) -> int:
        elapsed = now_ms - self._config.epoch_ms
        return (
            (elapsed << TIMESTAMP_SHIFT)
            | (self._config.datacenter_id << DATACENTER_SHIFT)
            | (self._config.worker_id << WORKER_SHIFT)
            | seq
        )

    def _current_ms(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_ms(self, last: int) -> int:
        now = self._current_ms()
        while now <= last:
            now = self._current_ms()
        return now
