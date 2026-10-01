import csv
import unittest

from green_ai_simulator.adapters.configuration.json_parser import parse_inventory_json
from green_ai_simulator.adapters.configuration.scenario_parser import parse_scenario_json
from green_ai_simulator.domain.inventory import validate_inventory
from green_ai_simulator.domain.engine import create_initial_state, compute_next_state
from green_ai_simulator.adapters.prometheus.exporter import SimulatorCollector


class HardwareInventoryTests(unittest.TestCase):
    def test_snapshot_matches_inventory_and_exports_all_nodes(self):
        inventory = parse_inventory_json('configs/inventory.hardware.json')
        validate_inventory(inventory)
        with open('configs/hardware.snapshot.csv', encoding='utf-8') as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(inventory.nodes), 50)
        self.assertEqual(sum(n.logical_cpus.value for n in inventory.nodes), 1952)
        for row, node in zip(rows, inventory.nodes):
            self.assertEqual(node.id, row['hardware_id'])
            self.assertEqual(node.logical_cpus.value, int(row['cpu_cores']))
            self.assertEqual(node.memory.value, int(row['ram_gb']) * 10**9)
        for profile in ('low', 'normal', 'high'):
            scenario = parse_scenario_json(f'configs/scenarios/{profile}.json')
            state = compute_next_state(inventory, scenario, create_initial_state(inventory), 42, 5)
            collector = SimulatorCollector(inventory, 'hardware-test')
            collector.update_state(state)
            samples = [s for family in collector.collect() for s in family.samples]
            self.assertEqual({s.labels['node'] for s in samples}, {r['hardware_id'] for r in rows})
            self.assertTrue(all(s.labels['origin'] == 'simulated' for s in samples))
