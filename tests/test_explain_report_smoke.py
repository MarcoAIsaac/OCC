from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _occ(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "occ.cli", *args],
        capture_output=True,
        text=True,
    )


def test_explain_report_smoke(tmp_path: Path) -> None:
    report_path = tmp_path / "judge_report.json"

    proc_judge = _occ(
        "judge",
        "examples/claim_specs/minimal_pass.yaml",
        "--json",
    )
    assert proc_judge.returncode == 0, proc_judge.stderr
    payload = json.loads(proc_judge.stdout)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    proc_explain = _occ("explain-report", str(report_path))
    assert proc_explain.returncode == 0, proc_explain.stderr
    assert "Verdict: PASS" in proc_explain.stdout or "Veredicto: PASS" in proc_explain.stdout
    assert "Pipeline:" in proc_explain.stdout or "Pipeline:" in proc_explain.stdout
    assert "Required checks:" in proc_explain.stdout or "Checks obligatorios:" in proc_explain.stdout
