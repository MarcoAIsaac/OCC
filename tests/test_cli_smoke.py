"""Smoke tests for the OCC CLI.

These tests are intentionally minimal: they validate that the project installs
correctly and that the `occ` entrypoint can execute.
"""

from __future__ import annotations

import subprocess


def test_occ_help() -> None:
    """`occ --help` should exit successfully."""
    proc = subprocess.run(["occ", "--help"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
