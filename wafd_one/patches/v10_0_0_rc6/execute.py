import frappe


def execute():
    """Expose operational projects and repair contracts saved without a project."""
    if frappe.db.exists("DocType", "WAFD Catering Project"):
        frappe.db.set_value(
            "DocType", "WAFD Catering Project",
            {
                "search_fields": "project_name,project_code,contract,mission,primary_hotel",
                "description": "مشروع WAFD التشغيلي المرتبط بالعقد / WAFD operational project linked to a contract",
            },
            update_modified=False,
        )

    from wafd_one.wafd_one.doctype.wafd_contract.wafd_contract import create_project_from_contract

    contracts = frappe.get_all(
        "WAFD Contract",
        filters={"project": ["is", "not set"]},
        fields=["name", "mission", "hotel", "start_date", "end_date"],
    )
    for row in contracts:
        if not all((row.mission, row.hotel, row.start_date, row.end_date)):
            continue
        try:
            create_project_from_contract(row.name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"WAFD rc6 project repair: {row.name}")

    frappe.clear_cache()
