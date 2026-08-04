import frappe


def execute():
    """Install RC79 inventory and undertaking visibility fixes safely."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking")

    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        # Before RC79 both checks defaulted to off although the approved company
        # signature and stamp were intended to appear on undertakings.
        frappe.db.sql(
            """update `tabWAFD Hotel Undertaking`
               set include_signature=1, include_stamp=1
               where ifnull(include_signature,0)=0 and ifnull(include_stamp,0)=0"""
        )

        if frappe.db.exists("DocType", "WAFD Print Settings"):
            settings = frappe.get_single("WAFD Print Settings")
            updates = {}
            if settings.default_signature:
                updates["signature_image"] = settings.default_signature
            if settings.default_stamp:
                updates["company_stamp"] = settings.default_stamp
            if updates:
                for name in frappe.get_all("WAFD Hotel Undertaking", pluck="name"):
                    current = frappe.db.get_value(
                        "WAFD Hotel Undertaking", name,
                        ["signature_image", "company_stamp"], as_dict=True,
                    )
                    values = {
                        key: value for key, value in updates.items()
                        if not current.get(key)
                    }
                    if values:
                        frappe.db.set_value(
                            "WAFD Hotel Undertaking", name, values,
                            update_modified=False,
                        )

    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()
    frappe.clear_cache()
