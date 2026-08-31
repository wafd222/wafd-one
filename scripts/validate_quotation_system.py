"""Static release checks for the standalone RC250 quotation system."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def permissions(meta):
    return {row["role"]: row for row in meta.get("permissions", [])}


def main():
    parent = load("wafd_one/wafd_one/doctype/wafd_quotation/wafd_quotation.json")
    child = load("wafd_one/wafd_one/doctype/wafd_quotation_item/wafd_quotation_item.json")
    print_format = load("wafd_one/wafd_one/print_format/wafd_quotation/wafd_quotation.json")
    fields = {row["fieldname"]: row for row in parent["fields"]}
    child_fields = {row["fieldname"]: row for row in child["fields"]}

    assert parent["name"] == "WAFD Quotation"
    assert child["name"] == "WAFD Quotation Item" and child["istable"] == 1
    assert parent["default_print_format"] == print_format["name"]
    assert fields["items"]["options"] == "WAFD Quotation Item"
    assert fields["include_signature"]["default"] == "1"
    assert fields["include_stamp"]["default"] == "1"
    assert fields["tax_rate"]["default"] == "15"
    for name in ("menu_source", "wafd_menu", "custom_menu_description", "daily_quantity", "service_days", "total_quantity", "unit_price", "amount"):
        assert name in child_fields

    perms = permissions(parent)
    required = {
        "System Manager": ("read", "write", "create", "delete"),
        "WAFD Operations Manager": ("read", "write", "create"),
        "WAFD Project Manager": ("read", "write", "create"),
        "WAFD Approver": ("read", "write"),
        "WAFD Finance User": ("read",),
        "WAFD Auditor": ("read",),
    }
    for role, capabilities in required.items():
        for capability in capabilities:
            assert perms[role].get(capability), f"{role} lacks {capability}"

    controller = (ROOT / "wafd_one/wafd_one/doctype/wafd_quotation/wafd_quotation.py").read_text(encoding="utf-8")
    client = (ROOT / "wafd_one/wafd_one/doctype/wafd_quotation/wafd_quotation.js").read_text(encoding="utf-8")
    html = print_format["html"]
    assert "tax_rate = 15" in controller and "tax_amount" in controller and "grand_total" in controller
    assert "APPROVAL_ROLES" in controller and "approve_quotation" in controller
    assert "self.signature_image = self.signature_image or signature" in controller
    assert "self.company_stamp = self.company_stamp or stamp" in controller
    assert 'add_asset_toggle(frm, "include_signature"' in client
    assert 'add_asset_toggle(frm, "include_stamp"' in client
    assert "frm.print_doc()" in client
    assert "doc.include_signature and doc.signature_image" in html
    assert "doc.include_stamp and doc.company_stamp" in html
    assert "get_doc(" not in html and "get_single(" not in html
    assert html.count("<style>") == html.count("</style>")

    hub = (ROOT / "wafd_one/wafd_one/page/wafd_documents_hub/wafd_documents_hub.js").read_text(encoding="utf-8")
    home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    assert '"doctype": "WAFD Quotation"' in hub
    assert 'new_doctype: "WAFD Quotation"' in home
    assert 'doctype: "WAFD Quotation"' in home
    assert "v10_0_0_rc250.execute" in (ROOT / "wafd_one/patches.txt").read_text(encoding="utf-8")
    print("RC250 quotation system validation passed")


if __name__ == "__main__":
    main()
