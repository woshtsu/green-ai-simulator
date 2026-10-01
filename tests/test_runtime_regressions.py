import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from dataclasses import dataclass

from green_ai_simulator.adapters.persistence.run_logger import RunLogger
from green_ai_simulator.application.runner import run_simulation
from green_ai_simulator.adapters.configuration.json_parser import parse_inventory_json
from green_ai_simulator.adapters.configuration.scenario_parser import parse_scenario_json
from green_ai_simulator.domain.engine import create_initial_state, compute_next_state
from green_ai_simulator.adapters.prometheus.exporter import SimulatorCollector


@dataclass
class Sample:
    value: str


class RuntimeRegressionTests(unittest.TestCase):
    def test_non_positive_duration_is_rejected_before_creating_run(self):
        args = SimpleNamespace(
            inventory="unused", scenario="unused", tick_seconds=1,
            duration_seconds=0, mode="offline", output_dir="unused", seed=1,
        )
        with patch("green_ai_simulator.application.runner.parse_inventory_json") as parse_inventory:
            self.assertEqual(run_simulation(args), 2)
            parse_inventory.assert_not_called()

    def test_logger_refuses_record_that_would_exceed_size_limit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RunLogger(temp_dir, "offline", 1, 1, 1, "inventory", "scenario")
            try:
                state = Sample(value="x" * 32)
                with patch("green_ai_simulator.adapters.persistence.run_logger.MAX_OUTPUT_BYTES", 1):
                    self.assertFalse(logger.write_sample(state))
                self.assertEqual(logger.metadata["bytes_written"], 0)
                self.assertEqual(Path(logger.samples_file).read_text(encoding="utf-8"), "")
            finally:
                logger.close()

    def test_seed_is_deterministic_and_exporter_labels_are_simulated(self):
        inventory = parse_inventory_json("configs/inventory.synthetic.json")
        scenario = parse_scenario_json("configs/scenarios/high.json")
        initial = create_initial_state(inventory)
        first = compute_next_state(inventory, scenario, initial, 42, 5)
        second = compute_next_state(inventory, scenario, initial, 42, 5)
        self.assertEqual(first, second)
        collector = SimulatorCollector(inventory, "test-run")
        collector.update_state(first)
        samples = [sample for family in collector.collect() for sample in family.samples]
        self.assertTrue(samples)
        for sample in samples:
            self.assertEqual(sample.labels["origin"], "simulated")
            self.assertEqual(sample.labels["cluster"], "sim-run-test-run")
            self.assertIn(sample.labels["node"], [node.id for node in inventory.nodes])
            self.assertGreaterEqual(sample.value, 0)


if __name__ == "__main__":
    unittest.main()
