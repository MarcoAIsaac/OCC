from __future__ import annotations

from occ import desktop


def test_desktop_has_main() -> None:
    assert callable(desktop.main)
