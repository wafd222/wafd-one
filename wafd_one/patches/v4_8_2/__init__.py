import frappe


def execute():
    """Install and validate the canonical searchable Single DocType console."""
    frappe.reload_doc(
        "wafd_one",
        "doctype",
        "wafd_administration_console",
        force=True,
        reset_permissions=True,
    )

    name = "WAFD Administration Console"
    if not frappe.db.exists("DocType", name):
        frappe.throw(f"{name} was not synchronized from the repository.")

    doc = frappe.get_doc("DocType", name)
    failures = []
    if not doc.issingle:
        failures.append("issingle must be enabled")
    if doc.module != "WAFD ONE":
        failures.append("module must be WAFD ONE")
    if getattr(doc, "custom", 0):
        failures.append("custom must be disabled")
    if getattr(doc, "hide_from_search", 0):
        failures.append("hide_from_search must be disabled")

    roles = {row.role for row in doc.permissions}
    for required_role in ("System Manager", "WAFD Operations Manager"):
        if required_role not in roles:
            failures.append(f"missing permission for {required_role}")

    if failures:
        frappe.throw(name + " validation failed: " + "; ".join(failures))

    from wafd_one.setup import rebuild_workspace_from_source

    rebuild_workspace_from_source()
    workspace = frappe.get_doc("Workspace", "WAFD ONE")
    valid_shortcut = any(
        row.label == "إدارة WAFD ONE"
        and row.type == "DocType"
        and row.link_to == name
        for row in workspace.shortcuts
    )
    if not valid_shortcut:
        frappe.throw("The main WAFD ONE workspace does not contain the administration console shortcut.")

    frappe.clear_cache()
