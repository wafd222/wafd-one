from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    role_home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    page = (ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home/wafd_storekeeper_home.js").read_text(encoding="utf-8")
    server = (ROOT / "wafd_one/storekeeper_portal.py").read_text(encoding="utf-8")
    block = role_home[role_home.index('role: "WAFD Storekeeper"'):role_home.index('role: "WAFD Cleaning Supervisor"')]

    assert block.count("action: \"storekeeper_") == 3
    assert "new_doctype" not in block and "cleaning_handover" not in block
    for action in ("receive", "handover", "inventory"):
        assert f'item.action === "storekeeper_{action}"' in role_home or "storekeeper_receive\", \"storekeeper_handover\", \"storekeeper_inventory" in role_home
        assert action in page
    for token in ("wafd-receipt-search", "wafd-handover-search", "wafd-recipient-role", "wafd-recipient-name"):
        assert token in page
    assert "row.full_name" in page
    assert '(row) => row.full_name, "اختر اسم المستلم"' in page
    assert "openMovement" not in page
    assert "Add row" not in page
    for function in ("get_storekeeper_workflow_options", "receive_inventory_materials", "create_employee_handover"):
        assert f"def {function}" in server
    for role in ("WAFD Cleaning Supervisor", "WAFD Production Supervisor", "WAFD Project Manager"):
        assert role in server
    assert "quantity > flt(balance.available_quantity)" in server
    assert "unit_cost < 0" in server
    print("RC268 practical Storekeeper validation passed")


if __name__ == "__main__":
    main()
