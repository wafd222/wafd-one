"""Install the non-destructive Iftar contract/delivery bridge."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_project", force=True)
    for page in (
        "wafd_delivery_supervisor",
        "wafd_iftar_operations",
        "wafd_iftar_wizard",
        "wafd_one_dashboard",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)

    # Historical Iftar trips remain valid standalone trips. No established
    # Iftar operation totals or workflow stages are changed by this patch.
    frappe.db.sql(
        """
        update `tabWAFD Delivery Trip`
        set iftar_link_type = case
            when ifnull(contract, '') != '' then 'مرتبط بعقد / Contract Linked'
            else 'بدون عقد / No Contract'
        end
        where meal_type = 'إفطار صائم / Iftar Saim'
          and (ifnull(iftar_link_type, '') = ''
               or iftar_link_type = 'غير إفطار صائم / Not Iftar')
        """
    )
    frappe.db.sql(
        """
        update `tabWAFD Iftar Project` ip
        inner join `tabWAFD Contract` c on c.name = ip.contract
        set ip.catering_project = c.project
        where ifnull(ip.contract, '') != ''
          and ifnull(ip.catering_project, '') = ''
          and ifnull(c.project, '') != ''
        """
    )
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="WAFD Iftar Project")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()
