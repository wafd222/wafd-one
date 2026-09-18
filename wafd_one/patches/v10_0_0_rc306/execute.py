"""Refresh cached page assets for employee-first Iftar duty assignment."""

import frappe


def execute():
    frappe.clear_cache()
