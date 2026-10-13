"""RC156: consolidate WAFD role permissions and remove stale manual overrides.

Repairs the permission drift found during Storekeeper, Production Supervisor and
Quality Inspector testing, normalizes supporting lookup access, and reloads the
role-aware operational forms so each role can execute only its own stage.
"""
import frappe

WAFD_ROLES = (
    "WAFD Operations Manager", "WAFD Project Manager", "WAFD Production Supervisor",
    "WAFD Quality Inspector", "WAFD Delivery Supervisor", "WAFD Driver",
    "WAFD Finance User", "WAFD Storekeeper", "WAFD Approver", "WAFD Auditor",
)
STANDARD_LOOKUPS = {
    "Item": {
        "WAFD Operations Manager": {"read":1,"select":1,"write":1,"create":1,"print":1,"report":1},
        "WAFD Storekeeper": {"read":1,"select":1,"print":1,"report":1},
        "WAFD Production Supervisor": {"read":1,"select":1,"print":1,"report":1},
        "WAFD Finance User": {"read":1,"select":1,"report":1},
    },
    "Item Group": {
        "WAFD Operations Manager": {"read":1,"select":1},
        "WAFD Storekeeper": {"read":1,"select":1},
        "WAFD Production Supervisor": {"read":1,"select":1},
    },
    "UOM": {
        "WAFD Operations Manager": {"read":1,"select":1},
        "WAFD Storekeeper": {"read":1,"select":1},
        "WAFD Production Supervisor": {"read":1,"select":1},
        "WAFD Finance User": {"read":1,"select":1},
    },
    "Warehouse": {
        "WAFD Operations Manager": {"read":1,"select":1},
        "WAFD Storekeeper": {"read":1,"select":1,"report":1},
        "WAFD Production Supervisor": {"read":1,"select":1},
    },
}
RIGHTS=("select","read","write","create","delete","submit","cancel","amend","print","email","report","import","export","share")

def execute():
    from wafd_one.setup import ALL_DOCTYPE_FILES, ensure_roles
    from frappe.permissions import setup_custom_perms
    ensure_roles()
    wafd_doctypes = frappe.get_all("DocType", filters={"name":["like","WAFD %"]}, pluck="name")
    if wafd_doctypes:
        frappe.db.delete("Custom DocPerm", {"parent":["in",wafd_doctypes]})
    for doctype_file in ALL_DOCTYPE_FILES:
        frappe.reload_doc("wafd_one","doctype",doctype_file,force=True,reset_permissions=True)
    for doctype, role_map in STANDARD_LOOKUPS.items():
        if not frappe.db.exists("DocType",doctype):
            continue
        setup_custom_perms(doctype)
        frappe.db.delete("Custom DocPerm", {"parent":doctype,"role":["in",list(WAFD_ROLES)]})
        for role, grants in role_map.items():
            row=frappe.get_doc({"doctype":"Custom DocPerm","parent":doctype,"parenttype":"DocType","parentfield":"permissions","role":role,"permlevel":0})
            for right in RIGHTS: row.set(right,int(grants.get(right,0)))
            row.insert(ignore_permissions=True)
    for page in ("wafd_one_dashboard","wafd_iftar_wizard","wafd_iftar_operations","wafd_iftar_report_center","wafd_launch_center"):
        frappe.reload_doc("wafd_one","page",page,force=True)
    frappe.clear_cache()
