from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    role_home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    start = role_home.index('role: "WAFD Storekeeper"')
    end = role_home.index('role: "WAFD Cleaning Supervisor"', start)
    storekeeper = role_home[start:end]
    assert "wafd-storekeeper-home" in storekeeper
    assert "استلام مواد مشتراة" in storekeeper
    assert "صرف مواد" in storekeeper
    assert "تحويل مواد" in storekeeper
    assert "إفطار صائم" not in storekeeper
    assert "Object.assign(doc, item.defaults || {})" in role_home

    page_root = ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home"
    page = json.loads((page_root / "wafd_storekeeper_home.json").read_text(encoding="utf-8"))
    roles = {row["role"] for row in page["roles"]}
    assert roles == {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}
    page_js = (page_root / "wafd_storekeeper_home.js").read_text(encoding="utf-8")
    assert "get_storekeeper_snapshot" in page_js
    assert "WAFD Purchase Order" in page_js
    assert "wafd-iftar-operations" not in page_js

    iftar_page = json.loads((ROOT / "wafd_one/wafd_one/page/wafd_iftar_operations/wafd_iftar_operations.json").read_text(encoding="utf-8"))
    assert "WAFD Storekeeper" not in {row["role"] for row in iftar_page["roles"]}
    iftar_project = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json").read_text(encoding="utf-8"))
    assert "WAFD Storekeeper" not in {row["role"] for row in iftar_project["permissions"]}

    form_js = (ROOT / "wafd_one/wafd_one/doctype/wafd_stock_movement/wafd_stock_movement.js").read_text(encoding="utf-8")
    assert "wafd_is_storekeeper_view" in form_js
    assert 'frm.toggle_display("reference_type", false)' in form_js
    assert "ترحيل وتحديث الرصيد" in form_js
    assert "create_goods_receipt" in form_js
    assert "تم تحميل المستودع والمواد والكميات تلقائيًا" in form_js

    server = (ROOT / "wafd_one/storekeeper_portal.py").read_text(encoding="utf-8")
    assert '"WAFD Storekeeper"' in server
    assert "ALLOWED_ROLES" in server
    print("RC264 storekeeper validation passed: role scope, simplified actions, balances and form")


if __name__ == "__main__":
    main()
