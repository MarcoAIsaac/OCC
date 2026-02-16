"""Smoke tests for the OCC CLI.

These tests are intentionally minimal: they validate that the project installs
correctly and that the `occ` entrypoint can execute.
"""

from __future__ import annotations

import subprocess
import sys


def _occ(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI using the current interpreter.

    This avoids PATH issues in CI environments.
    """

    return subprocess.run(
        [sys.executable, "-m", "occ.cli", *args],
        capture_output=True,
        text=True,
    )


def test_occ_help() -> None:
    """`occ --help` should exit successfully."""
    proc = _occ("--help")
    assert proc.returncode == 0, proc.stderr


def test_occ_list() -> None:
    proc = _occ("list", "--suite", "canon")
    assert proc.returncode == 0, proc.stderr
    assert "mrd_" in proc.stdout


def test_occ_predict_list() -> None:
    proc = _occ("predict", "list")
    assert proc.returncode == 0, proc.stderr
    assert "P-0003" in proc.stdout


def test_occ_judge_minimal_pass() -> None:
    proc = _occ("judge", "examples/claim_specs/minimal_pass.yaml")
    assert proc.returncode == 0, proc.stderr
    assert "PASS" in proc.stdout


def test_occ_judge_nuclear_pass() -> None:
    proc = _occ("judge", "examples/claim_specs/nuclear_pass.yaml", "--profile", "nuclear")
    assert proc.returncode == 0, proc.stderr
    assert "PASS" in proc.stdout


def test_occ_judge_json_contract() -> None:
    proc = _occ("judge", "examples/claim_specs/minimal_pass.yaml", "--json")
    assert proc.returncode == 0, proc.stderr
    assert "\"schema\": \"occ.judge_report.v1\"" in proc.stdout


def test_occ_verify_extensions_strict() -> None:
    proc = _occ("verify", "--suite", "extensions", "--strict", "--timeout", "60")
    assert proc.returncode == 0, proc.stderr
