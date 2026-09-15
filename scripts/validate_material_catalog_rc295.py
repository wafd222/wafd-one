"""Static and catalogue-integrity checks for RC295."""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_catalogue():
    namespace = {}
    exec((ROOT / "wafd_one/material_catalog_rc295.py").read_text(encoding="utf-8"), namespace)
    return namespace["CATALOGUE"]


catalogue = load_catalogue()
names = [row["ingredient_name"] for row in catalogue]
codes = [row["item_code"] for row in catalogue]
assert len(catalogue) >= 500, len(catalogue)
assert not [name for name, count in Counter(names).items() if count > 1]
assert len(codes) == len(set(codes))

required = {
    "برتقال": ("فواكه / Fruits", "ثلاجة 1 - الخضار والفواكه"),
    "بامية": ("خضار / Vegetables", "ثلاجة 1 - الخضار والفواكه"),
    "فواكه مجففة": ("تمور ومكسرات / Dates & Nuts", "ثلاجة 3 - المشروبات والعصيرات والماء والزبادي والتمور"),
    "مكسرات": ("تمور ومكسرات / Dates & Nuts", "ثلاجة 3 - المشروبات والعصيرات والماء والزبادي والتمور"),
    "أكياس سكر": ("مشروبات / Beverages", "مستودع 8 - المياه والمشروبات الكرتونية"),
    "حليب طويل الأجل": ("ألبان / Dairy", "ثلاجة 3 - المشروبات والعصيرات والماء والزبادي والتمور"),
    "دقيق أبيض": ("دقيق ومطاحن / Flour & Milling", "مستودع 3 - المواد الغذائية الجافة"),
    "قدر ستانلس 40 لتر": ("أواني ومعدات / Utensils & Equipment", "مستودع 6 - الأواني والمعدات"),
    "علبة وجبة رئيسية 3 أقسام": ("تغليف / Packaging", "مستودع 2 - التغليف"),
    "منظف أرضيات": ("منظفات / Cleaning", "مستودع 7 - أدوات النظافة"),
}
by_name = {row["ingredient_name"]: row for row in catalogue}
for name, (category, warehouse) in required.items():
    assert by_name[name]["category"] == category
    assert by_name[name]["preferred_warehouse"] == warehouse

# Every legacy generated material must be corrected by the curated catalogue.
tree = ast.parse((ROOT / "wafd_one/rc14_catalog.py").read_text(encoding="utf-8"))
legacy = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ADDITIONAL_INGREDIENTS" for t in node.targets):
        legacy = ast.literal_eval(node.value)
assert legacy and not ({row[0] for row in legacy} - set(names))

doctype = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_ingredient/wafd_ingredient.json").read_text(encoding="utf-8"))
category_options = next(field["options"].splitlines() for field in doctype["fields"] if field["fieldname"] == "category")
assert not ({row["category"] for row in catalogue} - set(category_options))

service = (ROOT / "wafd_one/storekeeper_portal.py").read_text(encoding="utf-8")
assert "i.preferred_warehouse=%s" in service
assert "limit 600" in service
assert "item.preferred_warehouse != target_warehouse" in service

page = (ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home/wafd_storekeeper_home.js").read_text(encoding="utf-8")
assert "refreshReceiptCategories" in page
assert "كل أقسام هذا المستودع" in page

patches = (ROOT / "wafd_one/patches.txt").read_text(encoding="utf-8")
assert "wafd_one.wafd_one.patches.v10_0_0_rc295.execute" in patches

print(f"RC295 material catalogue checks passed: {len(catalogue)} materials, {len(set(row['category'] for row in catalogue))} sections")

