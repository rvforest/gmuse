from __future__ import annotations

import subprocess
import sys


def test_normal_gmuse_import_does_not_import_inspect_or_create_artifacts(
    tmp_path,
) -> None:
    script = "import sys; import gmuse.commit; assert not any(k.startswith('inspect_ai') for k in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".gmuse-evals").exists()
