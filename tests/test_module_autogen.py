from __future__ import annotations

from pathlib import Path

import pytest

from occ.module_autogen import auto_generate_module
from occ.suites import SUITE_EXTENSIONS


def _bootstrap_repo(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    ext = tmp_path / SUITE_EXTENSIONS
    ext.mkdir(parents=True, exist_ok=True)
    (ext / "manifest.yaml").write_text("version: 1\n\nmodules: []\n", encoding="utf-8")
    pred_root = tmp_path / "predictions"
    pred_root.mkdir(parents=True, exist_ok=True)
    (pred_root / "registry.yaml").write_text("version: 1\npredictions: []\n", encoding="utf-8")


def test_auto_generate_module_and_prediction_draft(tmp_path: Path) -> None:
    _bootstrap_repo(tmp_path)
    claim = tmp_path / "claim.yaml"
    claim.write_text(
        "\n".join(
            [
                "claim_id: CLAIM-001",
                "title: Test generated module",
                "domain:",
                "  omega_I: test-domain",
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

    out = auto_generate_module(
        claim_path=claim,
        start=tmp_path,
        with_research=False,
        create_prediction=True,
        publish_prediction=False,
    )
    assert out["created"] is True
    module_dir = Path(str(out["module_dir"]))
    assert (module_dir / "scripts").is_dir()
    assert (module_dir / "inputs" / "pass.yaml").is_file()
    assert (module_dir / "module_context.json").is_file()
    assert out["prediction_draft"] is not None
    assert Path(str(out["prediction_draft"])).is_file()

    manifest = (tmp_path / SUITE_EXTENSIONS / "manifest.yaml").read_text(encoding="utf-8")
    assert str(out["module"]) in manifest


def test_auto_generate_detects_existing_module(tmp_path: Path) -> None:
    _bootstrap_repo(tmp_path)
    existing = tmp_path / SUITE_EXTENSIONS / "mrd_existing"
    existing.mkdir(parents=True, exist_ok=True)
    (existing / "scripts").mkdir(exist_ok=True)
    (existing / "scripts" / "run_mrd_existing.py").write_text("print('ok')\n", encoding="utf-8")

    claim = tmp_path / "claim.yaml"
    claim.write_text(
        "\n".join(
            [
                "claim_id: CLAIM-002",
                "title: Existing module mapping",
                "module: mrd_existing",
                "domain:",
                "  omega_I: test-domain",
                "  observables:",
                "    - O1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    out = auto_generate_module(claim_path=claim, start=tmp_path, with_research=False)
    assert out["created"] is False
    assert out["matched_existing"] is True
    assert out["module"] == "mrd_existing"


def test_auto_generate_validates_claim_shape(tmp_path: Path) -> None:
    _bootstrap_repo(tmp_path)
    claim = tmp_path / "invalid_claim.yaml"
    claim.write_text(
        "\n".join(
            [
                "claim_id: CLAIM-003",
                "title: \"\"",
                "domain:",
                "  omega_I: demo",
                "  observables: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not valid for module auto-generation"):
        auto_generate_module(claim_path=claim, start=tmp_path, with_research=False)
