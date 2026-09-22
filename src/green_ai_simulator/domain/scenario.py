from dataclasses import dataclass
from green_ai_simulator.domain.inventory import ValidationError

@dataclass(frozen=True)
class Scenario:
    schema_version: str
    name: str
    description: str
    
    # Intensidad base (0.0 a 1.0)
    base_cpu_utilization: float
    base_memory_utilization: float
    
    # Tasa base de red (bytes por segundo)
    base_network_tx_bytes_per_sec: int
    base_network_rx_bytes_per_sec: int
    
    # Tasa base de escritura en disco (bytes por segundo)
    base_disk_write_bytes_per_sec: int
    
    # Factor de ruido/perturbación (0.0 a 1.0)
    noise_factor: float

def validate_scenario(scenario: Scenario):
    if scenario.schema_version != "1.0":
        raise ValidationError(f"Unsupported scenario schema_version: '{scenario.schema_version}'")
        
    if not (0.0 <= scenario.base_cpu_utilization <= 1.0):
        raise ValidationError("base_cpu_utilization must be between 0.0 and 1.0")
        
    if not (0.0 <= scenario.base_memory_utilization <= 1.0):
        raise ValidationError("base_memory_utilization must be between 0.0 and 1.0")
        
    if scenario.base_network_tx_bytes_per_sec < 0 or scenario.base_network_rx_bytes_per_sec < 0:
        raise ValidationError("Network rates cannot be negative")
        
    if scenario.base_disk_write_bytes_per_sec < 0:
        raise ValidationError("Disk write rate cannot be negative")
        
    if not (0.0 <= scenario.noise_factor <= 1.0):
        raise ValidationError("noise_factor must be between 0.0 and 1.0")
