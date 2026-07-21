from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    version = "6.1.0"
    assert f'version = "{version}"' in (ROOT / "pyproject.toml").read_text()
    assert f'__version__ = "{version}"' in (ROOT / "wafd_one/__init__.py").read_text()
    assert (ROOT / f"RELEASE_NOTES_{version}.md").exists()

    for path in ROOT.rglob("*.py"):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for path in ROOT.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))

    required = {
        "WAFD Invoice",
        "WAFD Invoice Item",
        "WAFD Payment",
        "WAFD Delivery Proof",
        "WAFD Catering Project",
    }
    found = {
        json.loads(path.read_text(encoding="utf-8")).get("name")
        for path in ROOT.rglob("*.json")
    }
    missing = required - found
    assert not missing, f"Missing required DocTypes: {sorted(missing)}"
    print(f"WAFD ONE {version} release validation passed")


if __name__ == "__main__":
    main()
