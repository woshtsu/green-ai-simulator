import hashlib
from typing import Dict
from green_ai_simulator.domain.inventory import Inventory, Node
from green_ai_simulator.domain.scenario import Scenario
from green_ai_simulator.domain.state import EngineState, NodeState, CpuState, MemoryState, NetworkState, FileSystemState

def derive_noise(seed: int, logical_time: int, node_id: str, resource_id: str) -> float:
    """
    Genera un valor determinista entre -1.0 y 1.0 basado en los parámetros.
    """
    key = f"v1|{seed}|{logical_time}|{node_id}|{resource_id}".encode('utf-8')
    h = hashlib.sha256(key).digest()
    # Usamos los primeros 4 bytes para generar un entero
    val = int.from_bytes(h[:4], byteorder='big')
    # Mapear val (0 a 2^32 - 1) a float (-1.0 a 1.0)
    max_val = 0xFFFFFFFF
    return (val / max_val) * 2.0 - 1.0

def _calculate_cpu_state(node: Node, current_cpu: CpuState, scenario: Scenario, dt: int, noise: float) -> CpuState:
    # Intensidad base con ruido
    utilization = scenario.base_cpu_utilization + (noise * scenario.noise_factor)
    # Clamp entre 0.0 y 1.0
    utilization = max(0.0, min(1.0, utilization))
    
    # dt se distribuye entre todos los cpus del nodo (total user_seconds = dt * logical_cpus * util)
    total_dt_across_cpus = dt * node.logical_cpus.value
    user_inc = total_dt_across_cpus * utilization
    idle_inc = total_dt_across_cpus * (1.0 - utilization)
    
    return CpuState(
        idle_seconds=current_cpu.idle_seconds + idle_inc,
        user_seconds=current_cpu.user_seconds + user_inc
    )

def _calculate_memory_state(node: Node, scenario: Scenario, noise: float) -> MemoryState:
    # Memory no acumula a lo largo del tiempo, su estado es absoluto basado en la carga
    utilization = scenario.base_memory_utilization + (noise * scenario.noise_factor)
    utilization = max(0.0, min(1.0, utilization))
    
    used_bytes = int(node.memory.value * utilization)
    available_bytes = node.memory.value - used_bytes
    
    return MemoryState(available_bytes=available_bytes)

def _calculate_network_state(
    net_def, current_net: NetworkState, scenario: Scenario, dt: int, noise_tx: float, noise_rx: float
) -> NetworkState:
    # TX
    tx_rate = scenario.base_network_tx_bytes_per_sec + (noise_tx * scenario.base_network_tx_bytes_per_sec * scenario.noise_factor)
    tx_rate = max(0.0, min(net_def.capacity.value, tx_rate))
    
    # RX
    rx_rate = scenario.base_network_rx_bytes_per_sec + (noise_rx * scenario.base_network_rx_bytes_per_sec * scenario.noise_factor)
    rx_rate = max(0.0, min(net_def.capacity.value, rx_rate))
    
    return NetworkState(
        tx_bytes_total=current_net.tx_bytes_total + int(tx_rate * dt),
        rx_bytes_total=current_net.rx_bytes_total + int(rx_rate * dt)
    )

def _calculate_fs_state(
    fs_def, current_fs: FileSystemState, scenario: Scenario, dt: int, noise: float
) -> FileSystemState:
    # El almacenamiento se va llenando o vaciando (base write bytes)
    # Por simplificación en este incremento, asumimos que siempre escribe (reduciendo free_bytes)
    write_rate = scenario.base_disk_write_bytes_per_sec + (noise * scenario.base_disk_write_bytes_per_sec * scenario.noise_factor)
    write_rate = max(0.0, write_rate)
    
    written_bytes = int(write_rate * dt)
    free_bytes = max(0, current_fs.free_bytes - written_bytes)
    
    return FileSystemState(
        free_bytes=free_bytes,
        error=False
    )

def create_initial_state(inventory: Inventory) -> EngineState:
    node_states = {}
    for node in inventory.nodes:
        net_states = {net.name: NetworkState(rx_bytes_total=0, tx_bytes_total=0) for net in node.interfaces}
        fs_states = {fs.mountpoint: FileSystemState(free_bytes=fs.capacity.value, error=False) for fs in node.filesystems}
        
        node_states[node.id] = NodeState(
            cpu=CpuState(idle_seconds=0.0, user_seconds=0.0),
            memory=MemoryState(available_bytes=node.memory.value),
            network=net_states,
            filesystems=fs_states
        )
    return EngineState(logical_time=0, nodes=node_states)

def compute_next_state(
    inventory: Inventory,
    scenario: Scenario,
    current_state: EngineState,
    seed: int,
    dt_seconds: int
) -> EngineState:
    
    next_time = current_state.logical_time + dt_seconds
    next_nodes: Dict[str, NodeState] = {}
    
    for node in inventory.nodes:
        c_state = current_state.nodes[node.id]
        
        # CPU
        noise_cpu = derive_noise(seed, next_time, node.id, "cpu")
        next_cpu = _calculate_cpu_state(node, c_state.cpu, scenario, dt_seconds, noise_cpu)
        
        # Memory
        noise_mem = derive_noise(seed, next_time, node.id, "mem")
        next_mem = _calculate_memory_state(node, scenario, noise_mem)
        
        # Network
        next_net = {}
        for net in node.interfaces:
            noise_tx = derive_noise(seed, next_time, node.id, f"net_{net.name}_tx")
            noise_rx = derive_noise(seed, next_time, node.id, f"net_{net.name}_rx")
            next_net[net.name] = _calculate_network_state(net, c_state.network[net.name], scenario, dt_seconds, noise_tx, noise_rx)
            
        # FileSystems
        next_fs = {}
        for fs in node.filesystems:
            noise_fs = derive_noise(seed, next_time, node.id, f"fs_{fs.mountpoint}")
            next_fs[fs.mountpoint] = _calculate_fs_state(fs, c_state.filesystems[fs.mountpoint], scenario, dt_seconds, noise_fs)
            
        next_nodes[node.id] = NodeState(
            cpu=next_cpu,
            memory=next_mem,
            network=next_net,
            filesystems=next_fs
        )
        
    return EngineState(logical_time=next_time, nodes=next_nodes)
