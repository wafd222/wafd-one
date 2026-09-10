from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    movement = load("wafd_one/wafd_one/doctype/wafd_stock_movement/wafd_stock_movement.json")
    fields = {row["fieldname"]: row for row in movement["fields"]}
    for field in (
        "material_category", "handover_status", "handover_sent_by", "handover_sent_on",
        "handover_received_by", "handover_received_on", "handover_rejection_reason",
    ):
        assert field in fields
    assert "منظفات / Cleaning" in fields["material_category"]["options"]
    assert fields["handover_status"]["read_only"] == 1

    usage = load("wafd_one/wafd_one/doctype/wafd_cleaning_material_usage/wafd_cleaning_material_usage.json")
    usage_fields = {row["fieldname"] for row in usage["fields"]}
    assert {"supervisor", "source_handover", "purpose", "location", "items"} <= usage_fields
    permissions = {row["role"]: row for row in usage["permissions"]}
    assert "WAFD Cleaning Supervisor" not in permissions
    assert permissions["WAFD Storekeeper"]["read"] == 1

    controller = (ROOT / "wafd_one/cleaning_portal.py").read_text(encoding="utf-8")
    for token in ("respond_cleaning_handover", "record_cleaning_usage", "reverse_posted_movement", "remaining_quantity"):
        assert token in controller
    usage_controller = (ROOT / "wafd_one/wafd_one/doctype/wafd_cleaning_material_usage/wafd_cleaning_material_usage.py").read_text(encoding="utf-8")
    assert "Quantity exceeds the supervisor custody balance" in usage_controller

    form_js = (ROOT / "wafd_one/wafd_one/doctype/wafd_stock_movement/wafd_stock_movement.js").read_text(encoding="utf-8")
    assert 'frm.set_query("ingredient", "items"' in form_js
    assert "latest_market_cost" in form_js and "standard_cost" in form_js
    assert "إرسال لمشرف النظافة وتحديث الرصيد" in form_js

    page_js = (ROOT / "wafd_one/wafd_one/page/wafd_cleaning_home/wafd_cleaning_home.js").read_text(encoding="utf-8")
    for language in ("ar", "en", "bn", "ur", "hi", "id", "fr", "ha", "sw", "uz"):
        assert f"{language}:" in page_js
    assert "wafd_one.cleaning_portal.get_cleaning_dashboard" in page_js

    storekeeper_server = (ROOT / "wafd_one/storekeeper_portal.py").read_text(encoding="utf-8")
    for token in ("get_cleaning_handover_options", "create_cleaning_handover", "can_issue"):
        assert token in storekeeper_server
    storekeeper_page = (ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home/wafd_storekeeper_home.js").read_text(encoding="utf-8")
    assert "openCleaningHandover" in storekeeper_page
    assert "wafd-cleaning-pick-row" in storekeeper_page
    assert "create_cleaning_handover" in storekeeper_page

    role_home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    assert "wafd-cleaning-home" in role_home
    cleaning_block = role_home[role_home.index('role: "WAFD Cleaning Supervisor"'):]
    cleaning_block = cleaning_block[:cleaning_block.index('role: "WAFD Delivery Supervisor"')]
    assert "WAFD Stock Movement" not in cleaning_block
    assert "WAFD Cleaning Material Usage" not in cleaning_block
    storekeeper_start = role_home.index('role: "WAFD Storekeeper"')
    cleaning_start = role_home.index('role: "WAFD Cleaning Supervisor"', storekeeper_start)
    assert "إفطار صائم" not in role_home[storekeeper_start:cleaning_start]
    print("RC266 validation passed: stock picker, restricted supervisor workflow, usage and languages")


if __name__ == "__main__":
    main()
