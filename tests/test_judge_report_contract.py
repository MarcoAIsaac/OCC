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


def test_judge_report_contains_compiler_layers() -> None:
    proc = _occ("judge", "examples/claim_specs/minimal_pass.yaml", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)

    assert payload["schema"] == "occ.judge_report.v1"
    assert payload["report_bundle_schema"] == "occ.verdict_bundle.v2"
    assert payload["claim_bundle"]["schema"] == "occ.claim_bundle.v1"
    assert payload["occ_ir"]["schema"] == "occ.ir.v1"
    assert payload["constraint_ir"]["schema"] == "occ.constraint_ir.v1"
    assert "domain_declared" in payload["constraint_ir"]["required_checks"]
    assert payload["pipeline_trace"]["passes"][0]["name"] == "parse_claim"
    assert payload["diagnostics"]["counts"]["pass"] >= 1


def test_judge_report_uv_no_eval_has_reason_catalog(tmp_path: Path) -> None:
    claim = tmp_path / "uv_no_eval.yaml"
    claim.write_text(
        """
claim_id: "CLAIM-UV-0001"
title: "UV no-eval demo"
domain:
  omega_I: "Demo domain"
  observables:
    - "O1"
parameters:
  - name: "theta_hidden"
    accessible: false
    affects_observables: true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    proc = _occ("judge", str(claim), "--json")
    assert proc.returncode == 1, proc.stderr
    payload = json.loads(proc.stdout)

    assert payload["verdict"].startswith("NO-EVAL")
    assert payload["first_reason"] == "UV1"
    categories = {row["category"] for row in payload["reason_catalog"]}
    labels = {row["label"] for row in payload["reason_catalog"]}
    assert "uv_projection" in categories
    assert "UV projection" in labels
    assert payload["diagnostics"]["counts"]["no_eval"] >= 1
