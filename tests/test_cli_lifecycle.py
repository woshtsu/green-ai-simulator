import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
import urllib.request


class CliLifecycleTests(unittest.TestCase):
    def command(self, output, mode, duration):
        return ["green-ai-simulator", "run", "--inventory", "configs/inventory.synthetic.json",
                "--scenario", "configs/scenarios/high.json", "--seed", "42", "--duration-seconds",
                str(duration), "--tick-seconds", "1", "--mode", mode, "--output-dir", output,
                "--host", "127.0.0.1", "--port", "19191"]

    def test_offline_completion_writes_manifest_and_samples(self):
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run(self.command(output, "offline", 3), capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = next(Path(output).glob("*/manifest.json"))
            self.assertEqual(json.loads(manifest.read_text())["status"], "COMPLETED")
            samples = [json.loads(line) for line in manifest.with_name("samples.jsonl").read_text().splitlines()]
            self.assertEqual([s["logical_time"] for s in samples], [0, 1, 2, 3])

    def test_realtime_exporter_and_graceful_termination(self):
        with tempfile.TemporaryDirectory() as output:
            process = subprocess.Popen(self.command(output, "realtime", 30), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                for _ in range(50):
                    try:
                        with urllib.request.urlopen("http://127.0.0.1:19191/metrics", timeout=1) as response:
                            body = response.read().decode()
                        if 'origin="simulated"' in body:
                            break
                    except OSError:
                        pass
                    time.sleep(0.1)
                else:
                    self.fail("Exporter did not expose simulated metrics")
                self.assertIn("node_cpu_seconds_total", body)
                process.terminate()
                _, error = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, error)
                manifest = next(Path(output).glob("*/manifest.json"))
                self.assertEqual(json.loads(manifest.read_text())["status"], "STOPPED")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
