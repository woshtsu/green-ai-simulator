import json
import uuid
import datetime
from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any

class RunLogger:
    def __init__(self, output_dir_base: str, mode: str, seed: int, duration_sec: int, tick_sec: int, inv_path: str, scn_path: str):
        self.uuid = str(uuid.uuid4())
        self.run_dir = Path(output_dir_base) / f"run-{self.uuid}"
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.samples_file = self.run_dir / "samples.jsonl"
        self.manifest_file = self.run_dir / "manifest.json"
        
        self.status = "CREATED"
        self.metadata = {
            "uuid": self.uuid,
            "mode": mode,
            "seed": seed,
            "duration_seconds": duration_sec,
            "tick_seconds": tick_sec,
            "inventory_path": inv_path,
            "scenario_path": scn_path,
            "status": self.status,
            "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "completed_at_utc": None,
            "stop_reason": None,
            "bytes_written": 0
        }
        self.samples_f = open(self.samples_file, "a", encoding="utf-8")
        self._write_manifest()
        
    def _write_manifest(self):
        tmp = self.manifest_file.with_suffix('.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
        tmp.replace(self.manifest_file)
        
    def update_status(self, new_status: str, reason: str = None):
        self.status = new_status
        self.metadata["status"] = self.status
        if reason:
            self.metadata["stop_reason"] = reason
        if new_status in ["COMPLETED", "STOPPED", "FAILED"]:
            self.metadata["completed_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._write_manifest()
        
    def write_sample(self, state: Any) -> bool:
        """Escribe un snapshot al jsonl. Retorna False si se excede el límite de tamaño."""
        # Limite duro de 100MB por seguridad
        if self.metadata["bytes_written"] > 100 * 1024 * 1024:
            return False
        
        line = json.dumps(asdict(state)) + "\n"
        b_len = len(line.encode('utf-8'))
        self.samples_f.write(line)
        self.metadata["bytes_written"] += b_len
        return True
        
    def close(self):
        if self.samples_f and not self.samples_f.closed:
            self.samples_f.close()
        self._write_manifest()
