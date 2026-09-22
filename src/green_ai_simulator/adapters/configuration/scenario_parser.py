import json
from typing import Any, Dict
from green_ai_simulator.domain.inventory import ValidationError
from green_ai_simulator.adapters.configuration.json_parser import _check_keys
from green_ai_simulator.domain.scenario import Scenario

def parse_scenario_json(json_path: str) -> Scenario:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON syntax in '{json_path}': {e}")
    except Exception as e:
         raise ValidationError(f"Error reading file '{json_path}': {e}")
         
    if not isinstance(raw_data, dict):
        raise ValidationError("Root of JSON must be a dictionary")
        
    _check_keys(raw_data, {
        "schema_version", "name", "description", 
        "base_cpu_utilization", "base_memory_utilization",
        "base_network_tx_bytes_per_sec", "base_network_rx_bytes_per_sec",
        "base_disk_write_bytes_per_sec", "noise_factor"
    }, "root")
    
    return Scenario(
        schema_version=str(raw_data.get("schema_version", "")),
        name=str(raw_data.get("name", "")),
        description=str(raw_data.get("description", "")),
        base_cpu_utilization=float(raw_data.get("base_cpu_utilization", 0.0)),
        base_memory_utilization=float(raw_data.get("base_memory_utilization", 0.0)),
        base_network_tx_bytes_per_sec=int(raw_data.get("base_network_tx_bytes_per_sec", 0)),
        base_network_rx_bytes_per_sec=int(raw_data.get("base_network_rx_bytes_per_sec", 0)),
        base_disk_write_bytes_per_sec=int(raw_data.get("base_disk_write_bytes_per_sec", 0)),
        noise_factor=float(raw_data.get("noise_factor", 0.0)),
    )
