import frappe
from frappe.utils import flt
from wafd_one.master_data import WAREHOUSES, preferred_warehouse_for_ingredient, _ensure_erp_warehouse, _default_company

LEGACY_RENAMES = {
    "المستودع الجاف 2 - البهارات والبقوليات": "مستودع 1 - البهارات",
    "مستودع التغليف": "مستودع 2 - التغليف",
    "المستودع الجاف 1 - الأرز والحبوب": "مستودع 3 - المواد الغذائية الجافة",
    "مستودع الوجبات الجاهزة": "مستودع 4 - المواد الغذائية المعبأة",
    "مستودع المواد التشغيلية": "مستودع 5 - مواد الاستعمال اليومي",
    "مستودع المشروبات": "مستودع 8 - المياه والمشروبات الكرتونية",
    "غرفة التبريد 2 - الخضار": "ثلاجة 1 - الخضار والفواكه",
    "غرفة التجميد 1 - الدواجن": "ثلاجة 2 - اللحوم والدواجن والأسماك",
    "غرفة التبريد 1 - الألبان": "ثلاجة 3 - المشروبات والعصيرات والماء والزبادي والتمور",
    "غرفة التجميد 2 - اللحوم": "ثلاجة 4 - المجمدات والمعجنات",
}


def _rename_warehouse(old, new):
    if not frappe.db.exists("WAFD Warehouse", old) or old == new:
        return
    if frappe.db.exists("WAFD Warehouse", new):
        # Preserve existing balances and references; merge only empty legacy master.
        refs = frappe.db.count("WAFD Stock Balance", {"warehouse": old}) + frappe.db.count("WAFD Stock Movement", {"source_warehouse": old}) + frappe.db.count("WAFD Stock Movement", {"target_warehouse": old})
        if not refs:
            frappe.delete_doc("WAFD Warehouse", old, ignore_permissions=True, force=True)
        return
    frappe.rename_doc("WAFD Warehouse", old, new, force=True, merge=False)


def execute():
    if not frappe.db.exists("DocType", "WAFD Warehouse"):
        return
    for old, new in LEGACY_RENAMES.items():
        _rename_warehouse(old, new)

    for name, warehouse_type, location in WAREHOUSES:
        if not frappe.db.exists("WAFD Warehouse", name):
            frappe.get_doc({"doctype":"WAFD Warehouse","warehouse_name":name,"warehouse_type":warehouse_type,"location":location,"status":"نشط / Active"}).insert(ignore_permissions=True)
        else:
            frappe.db.set_value("WAFD Warehouse", name, {"warehouse_type":warehouse_type,"location":location,"status":"نشط / Active"}, update_modified=False)

    company = _default_company()
    if company:
        for name, _type, _location in WAREHOUSES:
            _ensure_erp_warehouse(name, company)

    if frappe.db.exists("DocType", "WAFD Ingredient"):
        for row in frappe.get_all("WAFD Ingredient", fields=["name","ingredient_name","category"]):
            preferred = preferred_warehouse_for_ingredient(row.ingredient_name or row.name, row.category)
            if frappe.get_meta("WAFD Ingredient").has_field("preferred_warehouse"):
                frappe.db.set_value("WAFD Ingredient", row.name, "preferred_warehouse", preferred, update_modified=False)
            # Create a zero balance placeholder in the correct warehouse. Existing
            # non-zero stock remains untouched; physical relocation must be posted
            # as a transfer to preserve the audit trail.
            if not frappe.db.exists("WAFD Stock Balance", {"warehouse":preferred,"ingredient":row.name}):
                uom = frappe.db.get_value("WAFD Ingredient", row.name, "uom")
                frappe.get_doc({"doctype":"WAFD Stock Balance","warehouse":preferred,"ingredient":row.name,"uom":uom,"actual_quantity":0,"reserved_quantity":0,"available_quantity":0,"average_cost":0,"stock_value":0,"count_status":"غير مجرود / Not Counted","stock_source_note":"RC61 preferred warehouse assignment; move physical stock through an approved transfer."}).insert(ignore_permissions=True)
