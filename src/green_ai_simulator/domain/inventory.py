import re
from dataclasses import dataclass
from typing import List, Literal, Any, Dict, Set

NAME_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")

OriginType = Literal["synthetic_fixture", "observed", "modeling_assumption"]

@dataclass(frozen=True)
class ValueWithOrigin:
    value: int
    unit: str
    origin: OriginType

@dataclass(frozen=True)
class NetworkInterface:
    name: str
    capacity: ValueWithOrigin

@dataclass(frozen=True)
class FileSystem:
    device: str
    mountpoint: str
    fstype: str
    capacity: ValueWithOrigin

@dataclass(frozen=True)
class Node:
    id: str
    logical_cpus: ValueWithOrigin
    memory: ValueWithOrigin
    interfaces: List[NetworkInterface]
    filesystems: List[FileSystem]

@dataclass(frozen=True)
class Inventory:
    schema_version: str
    cluster_name: str
    description: str
    nodes: List[Node]

class ValidationError(Exception):
    pass

LIMITS = {
    "max_nodes": 100,
    "max_total_cpus": 1000,
    "max_interfaces_per_node": 10,
    "max_fs_per_node": 20,
}

def validate_inventory(inv: Inventory) -> None:
    """Valida las reglas de negocio del inventario."""
    if inv.schema_version != "1.0":
        raise ValidationError(f"Unsupported schema_version: '{inv.schema_version}' (expected '1.0')")
    
    if not NAME_REGEX.match(inv.cluster_name):
        raise ValidationError(f"Invalid cluster_name: '{inv.cluster_name}'")
        
    if len(inv.nodes) > LIMITS["max_nodes"]:
        raise ValidationError(f"Limit exceeded: Too many nodes ({len(inv.nodes)} > {LIMITS['max_nodes']})")
        
    total_cpus = 0
    node_ids: Set[str] = set()
    
    for node in inv.nodes:
        if not NAME_REGEX.match(node.id):
            raise ValidationError(f"Invalid node id: '{node.id}'")
            
        if node.id in node_ids:
            raise ValidationError(f"Duplicate node id: '{node.id}'")
        node_ids.add(node.id)
        
        if node.logical_cpus.value <= 0:
            raise ValidationError(f"Node '{node.id}' has invalid logical CPUs: {node.logical_cpus.value}")
        if node.logical_cpus.unit != "count":
             raise ValidationError(f"Node '{node.id}' CPUs must have unit 'count', got '{node.logical_cpus.unit}'")
        
        total_cpus += node.logical_cpus.value
        
        if node.memory.value <= 0:
            raise ValidationError(f"Node '{node.id}' has invalid memory: {node.memory.value}")
        if node.memory.unit != "bytes":
             raise ValidationError(f"Node '{node.id}' memory must have unit 'bytes', got '{node.memory.unit}'")
             
        if len(node.interfaces) > LIMITS["max_interfaces_per_node"]:
            raise ValidationError(f"Limit exceeded: Node '{node.id}' has too many interfaces ({len(node.interfaces)})")
            
        if len(node.filesystems) > LIMITS["max_fs_per_node"]:
            raise ValidationError(f"Limit exceeded: Node '{node.id}' has too many filesystems ({len(node.filesystems)})")
            
        ifnames: Set[str] = set()
        for i in node.interfaces:
            if i.name in ifnames:
                raise ValidationError(f"Node '{node.id}' has duplicate interface: '{i.name}'")
            ifnames.add(i.name)
            if i.capacity.value <= 0:
                 raise ValidationError(f"Node '{node.id}' interface '{i.name}' has invalid capacity: {i.capacity.value}")
            if i.capacity.unit != "bytes_per_second":
                 raise ValidationError(f"Node '{node.id}' interface '{i.name}' must have unit 'bytes_per_second'")
                 
        fs_devices: Set[str] = set()
        fs_mounts: Set[str] = set()
        for f in node.filesystems:
            if f.device in fs_devices:
                raise ValidationError(f"Node '{node.id}' duplicate device: '{f.device}'")
            if f.mountpoint in fs_mounts:
                raise ValidationError(f"Node '{node.id}' duplicate mountpoint: '{f.mountpoint}'")
            fs_devices.add(f.device)
            fs_mounts.add(f.mountpoint)
            
            if f.capacity.value <= 0:
                 raise ValidationError(f"Node '{node.id}' fs '{f.device}' has invalid capacity: {f.capacity.value}")
            if f.capacity.unit != "bytes":
                 raise ValidationError(f"Node '{node.id}' fs '{f.device}' must have unit 'bytes'")
                 
    if total_cpus > LIMITS["max_total_cpus"]:
        raise ValidationError(f"Limit exceeded: Total CPUs exceed limit ({total_cpus} > {LIMITS['max_total_cpus']})")
