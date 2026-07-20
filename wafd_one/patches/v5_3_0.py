import frappe


def execute():
    """Migration-safe normalization for the contract-driven operation engine."""
    if frappe.db.table_exists("WAFD Catering Project"):
        frappe.db.sql("""
            update `tabWAFD Catering Project`
               set project_type='إعاشة فندقية / Hotel Catering'
             where ifnull(project_type, '')=''
        """)
    # Repair one-sided links without changing existing valid relationships.
    if frappe.db.table_exists("WAFD Contract") and frappe.db.table_exists("WAFD Catering Project"):
        rows = frappe.db.sql("""
            select c.name, c.project
              from `tabWAFD Contract` c
             where ifnull(c.project, '')!=''
        """, as_dict=True)
        for row in rows:
            current = frappe.db.get_value("WAFD Catering Project", row.project, "contract")
            if not current:
                frappe.db.set_value("WAFD Catering Project", row.project, "contract", row.name, update_modified=False)
