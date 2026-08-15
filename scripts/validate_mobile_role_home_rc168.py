from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def roles(doc):
    return {r["role"] for r in doc.get("roles", [])}


def main():
    dashboard = load("wafd_one/wafd_one/page/wafd_one_dashboard/wafd_one_dashboard.json")
    assert roles(dashboard) == {"System Manager", "WAFD Operations Manager"}

    role_home = load("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.json")
    required = {
        "System Manager", "WAFD Operations Manager", "WAFD Project Manager",
        "WAFD Production Supervisor", "WAFD Quality Inspector", "WAFD Storekeeper",
        "WAFD Cleaning Supervisor", "WAFD Delivery Supervisor", "WAFD Driver",
        "WAFD Finance User", "WAFD Approver", "WAFD Auditor",
    }
    assert required <= roles(role_home)

    hooks = (ROOT / "wafd_one/hooks.py").read_text(encoding="utf-8")
    assert 'app_home = "/desk/wafd-role-home"' in hooks
    assert '"route": "/desk/wafd-role-home"' in hooks

    sidebar = load("wafd_one/workspace_sidebar/wafd_one.json")
    assert sidebar["items"][0]["link_to"] == "wafd-role-home"
    setup = (ROOT / "wafd_one/setup.py").read_text(encoding="utf-8")
    assert '"link_to": "wafd-role-home"' in setup
    assert "ensure_rc168_mobile_role_navigation" in setup
    assert '{"page": "wafd-one-dashboard"}' in setup

    js = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    css = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.css").read_text(encoding="utf-8")
    for role in required:
        assert role in js, role
    assert 'WAFD Finance User' in js and 'WAFD Invoice' in js and 'WAFD Payment' in js
    assert 'WAFD Driver' in js and 'WAFD Delivery Trip' in js
    assert 'WAFD Cleaning Supervisor' in js and 'مستودع 7 - أدوات النظافة' in js
    assert '@media(max-width:900px)' in css
    assert 'wafd-mobile-hero' in css and 'wafd-mobile-card' in css

    dashboard_js = (ROOT / "wafd_one/wafd_one/page/wafd_one_dashboard/wafd_one_dashboard.js").read_text(encoding="utf-8")
    assert 'frappe.set_route("wafd-role-home")' in dashboard_js

    master = load("wafd_one/wafd_one/page/wafd_master_data_hub/wafd_master_data_hub.json")
    documents = load("wafd_one/wafd_one/page/wafd_documents_hub/wafd_documents_hub.json")
    assert "WAFD Finance User" not in roles(master)
    assert "WAFD Finance User" not in roles(documents)
    assert "WAFD Driver" not in roles(documents)

    print("RC168 mobile role-home and executive Page hardening validation passed")


if __name__ == "__main__":
    main()
