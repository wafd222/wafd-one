from __future__ import annotations

import copy
import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
APPROVED_BASE_LAYOUT = {
    "intro": {"y": 168, "h": 180},
    "details": {"y": 360, "h": 265},
    "terms": {"y": 610, "h": 170},
    "signatory": {"y": 790, "h": 82},
    "signature": {"y": 785, "h": 90},
    "stamp": {"y": 770, "h": 120},
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
        if block.get("id") in APPROVED_BASE_LAYOUT:
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
    live_migration = load_module(
        "wafd_rc261_layout",
        ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc261/execute.py",
    )
    restore = load_module(
        "wafd_rc262_layout",
        ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc262/execute.py",
    )

    current = source.undertaking_canvas()
    by_id = {block["id"]: block for block in current["blocks"]}
    for block_id, expected in APPROVED_BASE_LAYOUT.items():
        assert {key: by_id[block_id][key] for key in ("y", "h")} == expected

    compact_base = copy.deepcopy(current)
    before_base_compaction = copy.deepcopy(compact_base)
    assert migration._tighten_spacing(compact_base) is True
    assert without_layout_coordinates(compact_base) == without_layout_coordinates(before_base_compaction)
    assert restore._restore_approved_layout(compact_base) is True
    assert compact_base == current
    assert restore._restore_approved_layout(compact_base) is False

    customized = copy.deepcopy(current)
    next(row for row in customized["blocks"] if row.get("id") == "details")["y"] = 320
    untouched = copy.deepcopy(customized)
    assert restore._restore_approved_layout(customized) is False
    assert customized == untouched

    live = copy.deepcopy(current)
    for block_id, position in live_migration.SOURCE_LAYOUT.items():
        block = next(row for row in live["blocks"] if row.get("id") == block_id)
        block.update(position)
    approved_live = copy.deepcopy(live)
    assert live_migration._tighten_live_layout(live) is True
    assert without_layout_coordinates(live) == without_layout_coordinates(approved_live)
    assert restore._restore_approved_layout(live) is True
    assert live == approved_live
    assert restore._restore_approved_layout(live) is False

    live_customized = copy.deepcopy(approved_live)
    next(row for row in live_customized["blocks"] if row.get("id") == "terms")["y"] = 590
    live_untouched = copy.deepcopy(live_customized)
    assert restore._restore_approved_layout(live_customized) is False
    assert live_customized == live_untouched

    navigation = (ROOT / "wafd_one/public/js/wafd_mobile_navigation.js").read_text(encoding="utf-8")
    bundle = (ROOT / "wafd_one/public/wafd_mobile_navigation.bundle.js").read_text(encoding="utf-8")
    assert navigation == bundle
    assert ".wafd-und-preview-overlay" in navigation

    print("Undertaking layout restore passed: approved geometry, content preserved, one preview back button")


if __name__ == "__main__":
    main()
