import frappe


def execute():
    """Apply RC81 print and undertaking repairs safely and idempotently."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking")
    frappe.reload_doc("wafd_one", "doctype", "wafd_receiving_note")

    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        frappe.db.sql(
            """update `tabWAFD Hotel Undertaking`
               set include_signature=1, include_stamp=1
               where ifnull(include_signature, 0)=0 and ifnull(include_stamp, 0)=0"""
        )
        if frappe.db.exists("DocType", "WAFD Print Settings"):
            settings = frappe.get_single("WAFD Print Settings")
            for name in frappe.get_all("WAFD Hotel Undertaking", pluck="name"):
                current = frappe.db.get_value(
                    "WAFD Hotel Undertaking", name,
                    ["signature_image", "company_stamp"], as_dict=True,
                )
                values = {}
                if not current.signature_image and settings.default_signature:
                    values["signature_image"] = settings.default_signature
                if not current.company_stamp and settings.default_stamp:
                    values["company_stamp"] = settings.default_stamp
                if values:
                    frappe.db.set_value(
                        "WAFD Hotel Undertaking", name, values, update_modified=False
                    )

    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()
    frappe.clear_cache()
