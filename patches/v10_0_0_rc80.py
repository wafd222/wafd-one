import json
import frappe


def execute():
    _update_workspace()


def _update_workspace():
    if not frappe.db.exists("Workspace", "WAFD ONE"):
        return
    doc = frappe.get_doc("Workspace", "WAFD ONE")
    wanted = [
        ("مشاريع إفطار الصائم", "WAFD Iftar Project", "DocType"),
        ("أصحاب السفر والمستلمون", "WAFD Iftar Recipient", "DocType"),
    ]
    existing = {(r.label, r.link_to) for r in doc.links if r.type == "Link"}
    for label, link_to, link_type in wanted:
        if (label, link_to) not in existing:
            doc.append("links", {"type":"Link", "label":label, "link_to":link_to, "link_type":link_type, "hidden":0, "onboard":0})
    shortcut_existing = {s.link_to for s in doc.shortcuts}
    for label, link_to, _ in wanted:
        if link_to not in shortcut_existing:
            doc.append("shortcuts", {"label":label, "link_to":link_to, "type":"DocType", "doc_view":"List", "color":"Orange"})
    doc.flags.ignore_permissions = True
    doc.save()
