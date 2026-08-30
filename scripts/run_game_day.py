#!/usr/bin/env python3
"""Run the reproducible baseline and three public reliability faults.

The command intentionally stores the measured JSON outputs beside the reports
so a reviewer can inspect the exact evidence used in the incident write-up.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(*args: str) -> str:
    completed = subprocess.run(
        [PYTHON, *args], cwd=ROOT, check=True, text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def main() -> None:
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    scenarios = ["healthy", "duplicate_pk", "volume_drop", "stale_kb"]
    evidence: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "student": "Phạm Đình Minh (2A202601979)",
        "scenarios": {},
    }
    for scenario in scenarios:
        run("scripts/reset_lab.py")
        if scenario != "healthy":
            run("scripts/inject_fault.py", scenario)
        output = run("scripts/run_baseline.py")
        metrics_path = reports / "latest_metrics.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        snapshot_path = reports / f"game-day-{scenario}.json"
        snapshot_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        evidence["scenarios"][scenario] = {
            "baseline_output": output.splitlines(),
            "metrics_file": str(snapshot_path.relative_to(ROOT)).replace("\\", "/"),
            "orders_rows": metrics["orders_rows"],
            "orders_failed_checks": metrics["failed_contract_checks"],
            "kb_failed_checks": metrics["kb_failed_contract_checks"],
            "row_count_anomaly": metrics["row_count_anomaly"]["is_anomaly"],
        }
    run("scripts/reset_lab.py")
    run("scripts/run_baseline.py")
    (reports / "public-fault-evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Game-day evidence written to reports/public-fault-evidence.json")


if __name__ == "__main__":
    main()
