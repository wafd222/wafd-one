import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_kitchen", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_contract", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_catering_project", force=True)

    # Create one immediately usable kitchen for existing sites.
    kitchen_name = "المطبخ الرئيسي لشركة وفد المدينة / WAFD Main Kitchen"
    if not frappe.db.exists("WAFD Kitchen", kitchen_name):
        warehouses = frappe.get_all("WAFD Warehouse", fields=["name"], order_by="creation asc", limit=1)
        warehouse = warehouses[0].name if warehouses else None
        frappe.get_doc({
            "doctype": "WAFD Kitchen",
            "kitchen_name": kitchen_name,
            "status": "نشط / Active",
            "location": "المدينة المنورة / Madinah",
            "daily_capacity": 10000,
            "production_lines": 1,
            "default_warehouse": warehouse,
        }).insert(ignore_permissions=True)

    # Recalculate existing contract financial fields using the v8.1 rule.
    for name in frappe.get_all("WAFD Contract", pluck="name"):
        doc = frappe.get_doc("WAFD Contract", name)
        doc._calculate_services()
        frappe.db.set_value("WAFD Contract", name, {
            "services_subtotal": doc.services_subtotal,
            "tax_amount": doc.tax_amount,
            "grand_total": doc.grand_total,
            "advance_amount": doc.advance_amount,
            "outstanding_contract_amount": doc.outstanding_contract_amount,
        }, update_modified=False)
