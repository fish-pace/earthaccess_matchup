"""Entry point for ``python -m examples``.

Runs all three example scripts in sequence.
"""

from __future__ import annotations

import runpy
from pathlib import Path

_HERE = Path(__file__).parent


def _run(name: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}\n")
    runpy.run_path(str(_HERE / f"{name}.py"), run_name="__main__")


if __name__ == "__main__":
    for script in ("basic_daily", "multi_file", "diagnostics"):
        _run(script)
