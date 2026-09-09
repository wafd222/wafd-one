from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
TARGET = "وعرض هذا التعهد للجهات المسؤولة"


def load_module(name: str, path: Path):
    sys.modules.setdefault("frappe", types.ModuleType("frappe"))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    migration = load_module(
        "wafd_rc263_phrase",
        ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc263/execute.py",
    )
    assert migration._remove_clause(
        "نأمل التواصل معنا من قبلنا، وعرض هذا التعهد للجهات المسؤولة."
    ) == "نأمل التواصل معنا من قبلنا."
    assert migration._remove_clause(
        "نأمل التواصل معنا من قبلنا، وعرض هذا التعهد للجهات المسؤولة عند الحاجة."
    ) == "نأمل التواصل معنا من قبلنا."
    assert migration._remove_clause("نص آخر") == "نص آخر"
    assert migration._remove_clause(None) is None

    source_files = [
        ROOT / "wafd_one/patches/v5_1_0/execute.py",
        ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc194/execute.py",
        ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc204/execute.py",
        ROOT / "wafd_one/wafd_one/doctype/wafd_print_settings/wafd_print_settings.py",
        ROOT / "wafd_one/wafd_one/doctype/wafd_print_settings/wafd_print_settings.json",
        ROOT / "wafd_one/wafd_one/print_format/wafd_hotel_undertaking/wafd_hotel_undertaking.json",
    ]
    for path in source_files:
        assert TARGET not in path.read_text(encoding="utf-8"), path

    json.loads(source_files[4].read_text(encoding="utf-8"))
    json.loads(source_files[5].read_text(encoding="utf-8"))
    print("Undertaking phrase removal passed: requested clause removed, other text preserved")


if __name__ == "__main__":
    main()
