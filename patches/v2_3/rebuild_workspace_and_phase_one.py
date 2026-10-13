import frappe
from wafd_one.setup import apply_setup


def execute():
    apply_setup(force_rebuild=True)
    frappe.db.commit()
