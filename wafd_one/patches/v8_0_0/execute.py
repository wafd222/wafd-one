import frappe


def execute():
    """Reload production-ready contract and project models safely."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_project_service", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_contract", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_catering_project", force=True)

    if frappe.db.exists("DocType", "WAFD Contract"):
        frappe.db.sql(
            """
            UPDATE `tabWAFD Contract`
               SET contract_type = COALESCE(NULLIF(contract_type, ''), project_type),
                   tax_rate = COALESCE(tax_rate, 15),
                   payment_due_days = COALESCE(payment_due_days, 30),
                   operation_priority = COALESCE(NULLIF(operation_priority, ''), 'عادية / Normal')
            """
        )
