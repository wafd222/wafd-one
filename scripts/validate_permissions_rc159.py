import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]

doc = json.loads((root / "wafd_one/wafd_one/doctype/wafd_production_batch/wafd_production_batch.json").read_text(encoding="utf-8"))
perm = next(x for x in doc["permissions"] if x.get("role") == "WAFD Production Supervisor")
for right in ("read", "write", "create", "select", "print", "report"):
    assert perm.get(right) == 1, (right, perm)
assert "project" in (doc.get("search_fields") or "")

page = json.loads((root / "wafd_one/wafd_one/page/wafd_production_batches/wafd_production_batches.json").read_text(encoding="utf-8"))
assert page["title"] == "WAFD Production Batch"
assert "WAFD Production Supervisor" in {x["role"] for x in page["roles"]}

workspace = json.loads((root / "wafd_one/wafd_one/workspace/wafd_one/wafd_one.json").read_text(encoding="utf-8"))
assert any(x.get("label") == "دفعات الإنتاج" and x.get("link_to") == "WAFD Production Batch" for x in workspace["shortcuts"])
blocks = json.loads(workspace["content"])
assert any(x.get("type") == "shortcut" and x.get("data", {}).get("shortcut_name") == "دفعات الإنتاج" for x in blocks)

patches = (root / "wafd_one/patches.txt").read_text(encoding="utf-8")
assert "wafd_one.patches.v10_0_0_rc159.execute" in patches
assert (root / "wafd_one/__init__.py").read_text(encoding="utf-8").strip() == '__version__ = "10.0.0rc159"'
assert 'version = "10.0.0rc159"' in (root / "pyproject.toml").read_text(encoding="utf-8")
print("RC159 static permission/navigation assertions: OK")
