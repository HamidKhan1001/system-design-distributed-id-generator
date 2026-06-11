from dataclasses import dataclass


@dataclass(frozen=True)
class NodeConfig:
    datacenter_id: int
    worker_id: int
    epoch_ms: int = 1_700_000_000_000

    def __post_init__(self):
        if not (0 <= self.datacenter_id <= 31):
            raise ValueError("datacenter_id must be 0-31")
        if not (0 <= self.worker_id <= 31):
            raise ValueError("worker_id must be 0-31")
