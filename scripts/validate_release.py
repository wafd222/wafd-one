from __future__ import annotations

import ast
import csv
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    init_text = (ROOT / "wafd_one/__init__.py").read_text(encoding="utf-8")
    assert f'__version__ = "{version}"' in init_text
    assert (ROOT / f"RELEASE_NOTES_{version}.md").exists()

    for path in ROOT.rglob("*.py"):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    json_docs = []
    for path in ROOT.rglob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        json_docs.append((path, doc))

    required = {
        "WAFD Invoice", "WAFD Invoice Item", "WAFD Payment",
        "WAFD Delivery Proof", "WAFD Catering Project",
        "WAFD Hotel Undertaking", "تعهد والتزام إعاشة — WAFD",
    }
    found = {doc.get("name") for _, doc in json_docs}
    missing = required - found
    assert not missing, f"Missing required metadata: {sorted(missing)}"

    print_format = next(doc for _, doc in json_docs if doc.get("name") == "تعهد والتزام إعاشة — WAFD")
    html = print_format.get("html") or ""
    assert "get_single" not in html
    assert not re.search(r"(?:\{\{|\{%)[^%}]*\bs\.", html), "Undefined print-settings variable 's'"
    assert "{% if true %}" not in html
    assert "company_stamp" in html and "signature_image" in html
    assert html.count("<style>") == html.count("</style>")

    admin = (ROOT / "wafd_one/administration.py").read_text(encoding="utf-8")
    for function_name in ("reset_demo_database", "clear_reference_data"):
        block = admin[admin.index(f"def {function_name}"):]
        block = block[:block.find("\n\ndef ") if "\n\ndef " in block else len(block)]
        assert "frappe.throw" in block
        assert "_delete_doctypes(" not in block

    hotels_file = ROOT / "wafd_one/reference_data/madinah_hotels_400_ota_review.csv"
    with hotels_file.open(encoding="utf-8-sig", newline="") as handle:
        hotels = list(csv.DictReader(handle))
    assert len(hotels) == 400, f"Expected 400 hotel rows, found {len(hotels)}"
    names = [(row.get("hotel_name") or "").strip().casefold() for row in hotels]
    assert all(names), "Blank hotel name found"
    assert len(names) == len(set(names)), "Exact duplicate hotel names found"

    patch_lines = [line.strip() for line in (ROOT / "wafd_one/patches.txt").read_text().splitlines()]
    assert "wafd_one.patches.v6_3_2.execute" in patch_lines
    assert "frappe.utils" not in html
    setup_text = (ROOT / "wafd_one/setup.py").read_text(encoding="utf-8")
    assert "ensure_hotel_undertaking_print_format()" in setup_text

    print(f"WAFD ONE {version} release validation passed")


if __name__ == "__main__":
    main()
