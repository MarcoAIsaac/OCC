from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from occ import desktop


def test_desktop_has_main() -> None:
    assert callable(desktop.main)


def test_desktop_script_headless_check() -> None:
    desktop_script = Path(__file__).resolve().parents[1] / "occ" / "desktop.py"
    proc = subprocess.run(
        [sys.executable, str(desktop_script), "--headless-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "ok"
