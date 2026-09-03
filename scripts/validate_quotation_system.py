"""Static release checks for the standalone RC258 quotation system."""

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
    assert fields["sent_on"]["fieldtype"] == "Datetime"
    assert fields["sent_by"]["options"] == "User"
    assert fields["menu_attachment"]["fieldtype"] == "Attach Image"
    assert fields["tax_rate"]["default"] == "15"
    for name in ("menu_source", "wafd_menu", "custom_menu_description", "daily_quantity", "service_days", "total_quantity", "unit_price", "amount"):
        assert name in child_fields

    perms = permissions(parent)
    required = {
        "System Manager": ("read", "write", "create", "delete"),
        "WAFD Operations Manager": ("read", "write", "create"),
        "WAFD Project Manager": ("read", "write", "create"),
        "WAFD Quotation Officer": ("read", "write", "create"),
        "WAFD Approver": ("read", "write"),
        "WAFD Finance User": ("read",),
        "WAFD Auditor": ("read",),
    }
    for role, capabilities in required.items():
        for capability in capabilities:
            assert perms[role].get(capability), f"{role} lacks {capability}"

    controller = (ROOT / "wafd_one/wafd_one/doctype/wafd_quotation/wafd_quotation.py").read_text(encoding="utf-8")
    client = (ROOT / "wafd_one/wafd_one/doctype/wafd_quotation/wafd_quotation.js").read_text(encoding="utf-8")
    html = (ROOT / "wafd_one/wafd_one/print_format/wafd_quotation/wafd_quotation.html").read_text(encoding="utf-8")
    assert "tax_rate = 15" in controller and "tax_amount" in controller and "grand_total" in controller
    assert "APPROVAL_ROLES" in controller and "approve_quotation" in controller
    assert "self.signature_image = self.signature_image or signature" in controller
    assert "self.company_stamp = self.company_stamp or stamp" in controller
    assert 'add_asset_toggle(frm, "include_signature"' in client
    assert 'add_asset_toggle(frm, "include_stamp"' in client
    assert "open_quotation_preview(frm)" in client
    assert "ملاءمة الشاشة" in client and "طباعة PDF" in client and "مشاركة PDF" in client
    assert "preview_quotation_html" in controller
    assert "generate_quotation_pdf" in controller
    assert "download_generated_pdf" in controller
    assert "_remove_quotation_blank_pages" in controller
    assert "_undertaking_asset" in controller
    assert html.count('class="quote-page') == 3
    assert "height:295mm" in html
    assert 'class="signature-image"' in html and "width:48mm" in html
    assert 'class="stamp-image"' in html and "width:58mm" in html
    assert "doc.introduction_text" in html and "doc.quotation_terms" in html
    assert "doc.payment_terms" in html and "doc.closing_text" in html
    assert "doc.include_signature and doc.signature_image" in html
    assert "doc.include_stamp and doc.company_stamp" in html
    assert "'حسب المنيو المرسل'" in html and "'As per attached menu'" in html
    assert "{% if doc.menu_attachment %}" in html
    assert 'class="menu-image" src="{{ doc.menu_attachment }}"' in html
    assert "3 / 3" in html and "المنيو المرفق" in html
    assert "'3' if doc.menu_attachment else '2'" in html
    assert "get_doc(" not in html and "get_single(" not in html
    assert html.count("<style>") == html.count("</style>")

    hub = (ROOT / "wafd_one/wafd_one/page/wafd_documents_hub/wafd_documents_hub.js").read_text(encoding="utf-8")
    home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    assert '"doctype": "WAFD Quotation"' in hub
    assert 'new_doctype: "WAFD Quotation"' in home
    assert 'doctype: "WAFD Quotation"' in home
    child_controller = ROOT / "wafd_one/wafd_one/doctype/wafd_quotation_item/wafd_quotation_item.py"
    assert child_controller.exists(), "Frappe v16 requires the child DocType Python module"
    assert "class WAFDQuotationItem(Document)" in child_controller.read_text(encoding="utf-8")
    patches = (ROOT / "wafd_one/patches.txt").read_text(encoding="utf-8")
    assert "v10_0_0_rc250.execute" in patches
    assert "v10_0_0_rc251.execute" in patches
    assert "v10_0_0_rc252.execute" in patches
    assert "v10_0_0_rc253.execute" in patches
    assert "v10_0_0_rc254.execute" in patches
    assert "v10_0_0_rc255.execute" in patches
    assert "v10_0_0_rc256.execute" in patches
    assert "v10_0_0_rc257.execute" in patches
    assert "v10_0_0_rc258.execute" in patches
    assert "v10_0_0_rc259.execute" in patches
    assert "48 ساعة" in fields["quotation_terms"]["default"]
    assert "50%" in fields["payment_terms"]["default"]
    assert "التحويل البنكي" in fields["payment_terms"]["default"]
    assert "سلامة الغذاء" in fields["closing_text"]["default"]
    setup = (ROOT / "wafd_one/setup.py").read_text(encoding="utf-8")
    assert "def ensure_quotation_print_format" in setup
    assert "ensure_quotation_print_format()" in setup
    assert "render_quotation_direct_actions(frm)" in client
    assert "open_sent_quotations" in client
    assert 'if (frm.is_dirty()) await frm.save();' in client
    assert 'quotation_api(frm, "mark_quotation_sent")' in client
    assert "def mark_quotation_sent" in controller
    assert 'sent_on: ["is", "set"]' in client
    assert "page_number_only" in controller and "re.fullmatch" in controller
    hub = (ROOT / "wafd_one/wafd_one/page/wafd_documents_hub/wafd_documents_hub.js").read_text(encoding="utf-8")
    assert "عروض الأسعار المرسلة" in hub and '"sent_on": ["is", "set"]' in hub
    role_home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    assert "العروض المرسلة" in role_home and 'sent_on: ["is", "set"]' in role_home
    assert all(token in html for token in ("font-weight:500", "font-size:10px", "font-size:9.3px", "color:#101010"))
    migration = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc254/execute.py").read_text(encoding="utf-8")
    assert "generated_pdf" in migration and "sent_on" in migration and "sent_by" in migration
    rc255 = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc255/execute.py").read_text(encoding="utf-8")
    assert "ensure_quotation_file_permissions" in rc255 and "ensure_roles" in rc255
    employee_backend = (ROOT / "wafd_one/employee_team.py").read_text(encoding="utf-8")
    employee_ui = (ROOT / "wafd_one/wafd_one/page/wafd_employee_team/wafd_employee_team.js").read_text(encoding="utf-8")
    setup = (ROOT / "wafd_one/setup.py").read_text(encoding="utf-8")
    assert '"WAFD Quotation Officer"' in employee_backend
    assert "def set_employee_roles" in employee_backend and "def _normalize_roles" in employee_backend
    assert 'method: "wafd_one.employee_team.set_employee_roles"' in employee_ui
    assert 'id="wafd-employee-roles"' in employee_ui and "input:checked" in employee_ui
    assert 'setup_custom_perms("File")' in setup
    assert all(role in setup for role in ("WAFD Operations Manager", "WAFD Project Manager", "WAFD Quotation Officer"))
    assert '"create": 1' in setup
    file_security = (ROOT / "wafd_one/undertaking_file_security.py").read_text(encoding="utf-8")
    assert 'QUOTATION_DOCTYPE = "WAFD Quotation"' in file_security
    assert "QUOTATION_FILE_CREATORS" in file_security
    assert 'permission_type == "create"' in file_security
    assert '{"menu_attachment", "generated_pdf"}' in file_security
    assert "frappe.has_permission" in file_security
    assert 'role: "WAFD Quotation Officer"' in role_home
    assert "const matchedProfiles" in role_home and "mergedItems" in role_home
    rc256 = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc256/execute.py").read_text(encoding="utf-8")
    assert "ensure_quotation_file_permissions" in rc256
    assert "ensure_quotation_print_format" in rc256
    assert "wafd_role_home" in rc256
    assert "فقط العروض التي تمت مشاركتها وتسجيل إرسالها" in role_home
    assert "المسودات والمعتمدة والمرسلة وجميع الحالات" in role_home
    assert "'Meal Count' if is_en else 'عدد الوجبات'" in html
    assert "<th>يومي</th>" not in html
    rc257 = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc257/execute.py").read_text(encoding="utf-8")
    assert "ensure_quotation_print_format" in rc257
    rc258 = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc258/execute.py").read_text(encoding="utf-8")
    assert 'reload_doc("wafd_one", "doctype", "wafd_quotation"' in rc258
    assert "quotation_language" in fields
    assert "quotation_subject_en" in fields
    assert "language == 'en'" in html
    assert "wafd-q-lang" in client
    assert "z-index:2147483000" in client
    print("RC258 bilingual quotation and preview-back validation passed")


if __name__ == "__main__":
    main()
