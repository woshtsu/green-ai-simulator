from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class CpuState:
    idle_seconds: float
    user_seconds: float

@dataclass(frozen=True)
class MemoryState:
    available_bytes: int

@dataclass(frozen=True)
class NetworkState:
    rx_bytes_total: int
    tx_bytes_total: int

@dataclass(frozen=True)
class FileSystemState:
    free_bytes: int
    error: bool

@dataclass(frozen=True)
class NodeState:
    # CPU total consolidada
    cpu: CpuState
    memory: MemoryState
    # Network interfaces per name
    network: Dict[str, NetworkState]
    # FileSystems per mountpoint
    filesystems: Dict[str, FileSystemState]

@dataclass(frozen=True)
class EngineState:
    logical_time: int
    # Node states per node id
    nodes: Dict[str, NodeState]
