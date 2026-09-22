import threading
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from green_ai_simulator.domain.state import EngineState
from green_ai_simulator.domain.inventory import Inventory

class SimulatorCollector:
    def __init__(self, inventory: Inventory, run_uuid: str):
        self.inventory = inventory
        # The plan says: "Usar cluster=sim-run-<uuid> para su identidad externa."
        self.cluster_name = f"sim-run-{run_uuid}"
        self.current_state: EngineState = None
        self._lock = threading.Lock()
        
    def update_state(self, state: EngineState):
        with self._lock:
            self.current_state = state
            
    def collect(self):
        with self._lock:
            state = self.current_state
            
        if state is None:
            return
            
        cpu_family = CounterMetricFamily(
            "node_cpu_seconds_total", 
            "Seconds the cpus spent in each mode.", 
            labels=["cluster", "node", "origin", "cpu", "mode"]
        )
        
        mem_total_family = GaugeMetricFamily(
            "node_memory_MemTotal_bytes", 
            "Memory information field MemTotal_bytes.", 
            labels=["cluster", "node", "origin"]
        )
        mem_avail_family = GaugeMetricFamily(
            "node_memory_MemAvailable_bytes", 
            "Memory information field MemAvailable_bytes.", 
            labels=["cluster", "node", "origin"]
        )
        
        net_rx_family = CounterMetricFamily(
            "node_network_receive_bytes_total", 
            "Network device statistic receive_bytes.", 
            labels=["cluster", "node", "origin", "device"]
        )
        net_tx_family = CounterMetricFamily(
            "node_network_transmit_bytes_total", 
            "Network device statistic transmit_bytes.", 
            labels=["cluster", "node", "origin", "device"]
        )
        
        fs_size_family = GaugeMetricFamily(
            "node_filesystem_size_bytes", 
            "Filesystem size in bytes.", 
            labels=["cluster", "node", "origin", "device", "mountpoint", "fstype"]
        )
        fs_free_family = GaugeMetricFamily(
            "node_filesystem_free_bytes", 
            "Filesystem free space in bytes.", 
            labels=["cluster", "node", "origin", "device", "mountpoint", "fstype"]
        )
        fs_error_family = GaugeMetricFamily(
            "node_filesystem_device_error", 
            "Whether an error occurred while getting statistics for the given device.", 
            labels=["cluster", "node", "origin", "device", "mountpoint", "fstype"]
        )

        for node_def in self.inventory.nodes:
            nid = node_def.id
            nstate = state.nodes.get(nid)
            if not nstate:
                continue
                
            # Memory
            mem_total_family.add_metric([self.cluster_name, nid, "simulated"], node_def.memory.value)
            mem_avail_family.add_metric([self.cluster_name, nid, "simulated"], nstate.memory.available_bytes)
            
            # CPU
            cores = node_def.logical_cpus.value
            user_per_core = nstate.cpu.user_seconds / cores
            idle_per_core = nstate.cpu.idle_seconds / cores
            
            for i in range(cores):
                cpu_id = str(i)
                cpu_family.add_metric([self.cluster_name, nid, "simulated", cpu_id, "user"], user_per_core)
                cpu_family.add_metric([self.cluster_name, nid, "simulated", cpu_id, "idle"], idle_per_core)
                
            # Network
            for net_def in node_def.interfaces:
                net_state = nstate.network.get(net_def.name)
                if net_state:
                    net_rx_family.add_metric([self.cluster_name, nid, "simulated", net_def.name], net_state.rx_bytes_total)
                    net_tx_family.add_metric([self.cluster_name, nid, "simulated", net_def.name], net_state.tx_bytes_total)
                    
            # FileSystems
            for fs_def in node_def.filesystems:
                fs_state = nstate.filesystems.get(fs_def.mountpoint)
                if fs_state:
                    labels = [self.cluster_name, nid, "simulated", fs_def.device, fs_def.mountpoint, fs_def.fstype]
                    fs_size_family.add_metric(labels, fs_def.capacity.value)
                    fs_free_family.add_metric(labels, fs_state.free_bytes)
                    fs_error_family.add_metric(labels, 1.0 if fs_state.error else 0.0)
                    
        yield cpu_family
        yield mem_total_family
        yield mem_avail_family
        yield net_rx_family
        yield net_tx_family
        yield fs_size_family
        yield fs_free_family
        yield fs_error_family
