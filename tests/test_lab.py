from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from occ.lab import LabConfig, run_experiment_lab


def test_run_experiment_lab_artifacts(tmp_path: Path) -> None:
    claim = tmp_path / "claim.yaml"
    claim.write_text(
        "\n".join(
            [
                "claim_id: CLAIM-LAB-001",
                "title: Lab pass claim",
                "domain:",
                "  omega_I: demo",
                "  observables:",
                "    - O1",
                "parameters:",
                "  - name: theta",
                "    accessible: true",
                "    affects_observables: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "lab_out"
    payload = run_experiment_lab(
        LabConfig(
            claim_paths=[claim],
            profiles=["core", "nuclear"],
            strict_trace=False,
            out_dir=out_dir,
        )
    )

    assert payload["schema"] == "occ.lab_report.v1"
    assert payload["totals"]["runs"] == 2
    artifacts = payload["artifacts"]
    assert Path(str(artifacts["json"])).is_file()
    assert Path(str(artifacts["results_csv"])).is_file()
    assert Path(str(artifacts["profile_csv"])).is_file()
    assert Path(str(artifacts["matrix_md"])).is_file()


def test_cli_lab_fail_on_non_pass(tmp_path: Path) -> None:
    out_dir = tmp_path / "lab_cli_out"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "occ.cli",
            "lab",
            "run",
            "--claims",
            "examples/claim_specs/nuclear_noeval.yaml",
            "--profiles",
            "nuclear",
            "--out",
            str(out_dir),
            "--fail-on-non-pass",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["totals"]["runs"] == 1
    assert payload["totals"]["no_eval"] >= 1
