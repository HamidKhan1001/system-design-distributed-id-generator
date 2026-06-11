import pytest
from idgen import SnowflakeGenerator, NodeConfig


@pytest.fixture
def gen():
    return SnowflakeGenerator(NodeConfig(datacenter_id=1, worker_id=1))


@pytest.fixture
def gen2():
    return SnowflakeGenerator(NodeConfig(datacenter_id=1, worker_id=2))
