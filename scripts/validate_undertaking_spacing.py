from __future__ import annotations

import copy
import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
TARGET_LAYOUT = {
    "intro": {"y": 168, "h": 105},
    "details": {"y": 285, "h": 265},
    "terms": {"y": 535, "h": 170},
    "signatory": {"y": 715, "h": 82},
    "signature": {"y": 710, "h": 90},
    "stamp": {"y": 695, "h": 120},
}


def load_module(name: str, path: Path):
    sys.modules.setdefault("frappe", types.ModuleType("frappe"))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def without_layout_coordinates(canvas):
    result = copy.deepcopy(canvas)
    for block in result["blocks"]:
        if block.get("id") in TARGET_LAYOUT:
            block.pop("y", None)
            block.pop("h", None)
    return result


def main() -> None:
    source = load_module(
        "wafd_rc38_layout",
        ROOT / "wafd_one/patches/v10_0_0_rc38/execute.py",
    )
    migration = load_module(
        "wafd_rc260_layout",
        ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc260/execute.py",
    )

    current = source.undertaking_canvas()
    by_id = {block["id"]: block for block in current["blocks"]}
    for block_id, expected in TARGET_LAYOUT.items():
        assert {key: by_id[block_id][key] for key in ("y", "h")} == expected

    legacy = copy.deepcopy(current)
    for block_id, position in migration.SOURCE_LAYOUT.items():
        block = next(row for row in legacy["blocks"] if row.get("id") == block_id)
        block.update(position)
    before = copy.deepcopy(legacy)
    assert migration._tighten_spacing(legacy) is True
    assert without_layout_coordinates(legacy) == without_layout_coordinates(before)
    assert legacy == current
    assert migration._tighten_spacing(legacy) is False

    customized = copy.deepcopy(before)
    next(row for row in customized["blocks"] if row.get("id") == "details")["y"] = 320
    untouched = copy.deepcopy(customized)
    assert migration._tighten_spacing(customized) is False
    assert customized == untouched

    print("Undertaking spacing validation passed: coordinates only, content preserved")


if __name__ == "__main__":
    main()
