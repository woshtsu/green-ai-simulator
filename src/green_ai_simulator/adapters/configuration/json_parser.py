import json
from typing import Any, Dict
from green_ai_simulator.domain.inventory import (
    Inventory, Node, NetworkInterface, FileSystem, ValueWithOrigin, ValidationError
)

def _check_keys(data: Dict[str, Any], allowed_keys: set, path: str):
    """Verifica que no haya claves desconocidas en el diccionario para detectar errores."""
    for key in data.keys():
        if key not in allowed_keys:
            raise ValidationError(f"Unknown key '{key}' found at {path}")

def _parse_value_with_origin(data: Any, path: str) -> ValueWithOrigin:
    if not isinstance(data, dict):
        raise ValidationError(f"Expected dict at {path}, got {type(data).__name__}")
    _check_keys(data, {"value", "unit", "origin"}, path)
    
    val = data.get("value")
    if not isinstance(val, int) or isinstance(val, bool):
         raise ValidationError(f"Invalid integer for 'value' at {path}")
         
    return ValueWithOrigin(
        value=val,
        unit=str(data.get("unit", "")),
        origin=str(data.get("origin", ""))
    )

def parse_inventory_json(json_path: str) -> Inventory:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON syntax in '{json_path}': {e}")
    except Exception as e:
         raise ValidationError(f"Error reading file '{json_path}': {e}")
         
    if not isinstance(raw_data, dict):
        raise ValidationError("Root of JSON must be a dictionary")
        
    _check_keys(raw_data, {"schema_version", "cluster_name", "description", "nodes"}, "root")
    
    nodes_data = raw_data.get("nodes", [])
    if not isinstance(nodes_data, list):
         raise ValidationError("'nodes' must be a list")
         
    parsed_nodes = []
    for i, n_data in enumerate(nodes_data):
        node_path = f"nodes[{i}]"
        if not isinstance(n_data, dict):
             raise ValidationError(f"Expected dict at {node_path}")
        
        _check_keys(n_data, {"id", "logical_cpus", "memory", "interfaces", "filesystems"}, node_path)
        
        # Parse interfaces
        if_data_list = n_data.get("interfaces", [])
        if not isinstance(if_data_list, list):
            raise ValidationError(f"'interfaces' must be a list at {node_path}")
        parsed_interfaces = []
        for j, if_data in enumerate(if_data_list):
            if_path = f"{node_path}.interfaces[{j}]"
            _check_keys(if_data, {"name", "capacity"}, if_path)
            parsed_interfaces.append(NetworkInterface(
                name=str(if_data.get("name", "")),
                capacity=_parse_value_with_origin(if_data.get("capacity"), f"{if_path}.capacity")
            ))
            
        # Parse filesystems
        fs_data_list = n_data.get("filesystems", [])
        if not isinstance(fs_data_list, list):
            raise ValidationError(f"'filesystems' must be a list at {node_path}")
        parsed_filesystems = []
        for j, fs_data in enumerate(fs_data_list):
            fs_path = f"{node_path}.filesystems[{j}]"
            _check_keys(fs_data, {"device", "mountpoint", "fstype", "capacity"}, fs_path)
            parsed_filesystems.append(FileSystem(
                device=str(fs_data.get("device", "")),
                mountpoint=str(fs_data.get("mountpoint", "")),
                fstype=str(fs_data.get("fstype", "")),
                capacity=_parse_value_with_origin(fs_data.get("capacity"), f"{fs_path}.capacity")
            ))
            
        parsed_nodes.append(Node(
            id=str(n_data.get("id", "")),
            logical_cpus=_parse_value_with_origin(n_data.get("logical_cpus"), f"{node_path}.logical_cpus"),
            memory=_parse_value_with_origin(n_data.get("memory"), f"{node_path}.memory"),
            interfaces=parsed_interfaces,
            filesystems=parsed_filesystems
        ))
        
    return Inventory(
        schema_version=str(raw_data.get("schema_version", "")),
        cluster_name=str(raw_data.get("cluster_name", "")),
        description=str(raw_data.get("description", "")),
        nodes=parsed_nodes
    )
