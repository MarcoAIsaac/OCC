import subprocess


def test_occ_help_exits_zero() -> None:
    result = subprocess.run(["occ", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
