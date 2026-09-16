import frappe


def execute():
    """Install reliable sent tracking and the clearer quotation typography."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    frappe.db.sql(
        """
        UPDATE `tabWAFD Quotation`
           SET sent_on = COALESCE(sent_on, generated_on, modified),
               sent_by = COALESCE(NULLIF(sent_by, ''), NULLIF(generated_by, ''), owner)
         WHERE sent_on IS NULL
           AND (
                COALESCE(generated_pdf, '') != ''
                OR status IN ('أرسل للعميل / Sent', 'مقبول / Accepted', 'مرفوض / Rejected')
           )
        """
    )
    from wafd_one.setup import ensure_quotation_print_format
    ensure_quotation_print_format()
    frappe.clear_cache(doctype="WAFD Quotation")
    frappe.clear_cache()
