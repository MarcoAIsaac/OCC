from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from occ.runner import extract_verdict_from_report, run_bundle
from occ.suites import SUITE_EXTENSIONS


def _write_runner(path: Path, code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(code), encoding="utf-8")


def _write_bundle(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("claim_id: TEST\n", encoding="utf-8")


def test_run_bundle_uses_new_report_not_stale(tmp_path: Path) -> None:
    suite = tmp_path / SUITE_EXTENSIONS
    module = suite / "mrd_fake"
    outputs = module / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    stale = outputs / "stale.report.json"
    stale.write_text(json.dumps({"verdict": "PASS(STALE)"}), encoding="utf-8")

    runner = module / "scripts" / "run_mrd_fake.py"
    _write_runner(
        runner,
        """
        import json
        from pathlib import Path

        out = Path(__file__).resolve().parents[1] / "outputs" / "fresh.report.json"
        out.write_text(json.dumps({"verdict": "PASS(FRESH)"}), encoding="utf-8")
        """,
    )

    bundle = module / "inputs" / "pass.yaml"
    _write_bundle(bundle)

    res = run_bundle(bundle, module="mrd_fake", suite="extensions")
    assert res.report_path is not None
    verdict = extract_verdict_from_report(Path(res.report_path))
    assert verdict == "PASS(FRESH)"


def test_run_bundle_timeout(tmp_path: Path) -> None:
    suite = tmp_path / SUITE_EXTENSIONS
    module = suite / "mrd_slow"
    runner = module / "scripts" / "run_mrd_slow.py"
    _write_runner(
        runner,
        """
        import time
        time.sleep(2.0)
        """,
    )

    bundle = module / "inputs" / "pass.yaml"
    _write_bundle(bundle)

    with pytest.raises(RuntimeError, match="timed out"):
        run_bundle(bundle, module="mrd_slow", suite="extensions", timeout=1)
