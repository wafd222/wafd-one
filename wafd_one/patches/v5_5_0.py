import frappe


def execute():
    if not frappe.db.table_exists("WAFD Purchase Order"):
        return
    from wafd_one.wafd_one.doctype.wafd_purchase_order.wafd_purchase_order import sync_purchase_order_receipts
    for name in frappe.get_all("WAFD Purchase Order", pluck="name"):
        sync_purchase_order_receipts(name)
