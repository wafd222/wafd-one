"""RC163: driver user linking and row-level delivery security."""
import frappe


def execute():
    # The DocType schema is synchronized before patches, so system_user exists here.
    if not frappe.db.exists("DocType", "WAFD Driver"):
        return

    # Auto-link only when the legacy site is unambiguous: exactly one WAFD Driver
    # role user and exactly one unlinked driver record. Otherwise an administrator
    # must select the System User explicitly on each driver record.
    role_users = frappe.get_all(
        "Has Role",
        filters={"role": "WAFD Driver", "parenttype": "User"},
        pluck="parent",
    )
    eligible = []
    for user in sorted(set(role_users)):
        row = frappe.db.get_value("User", user, ["enabled", "user_type"], as_dict=True)
        if row and row.enabled and row.user_type == "System User":
            eligible.append(user)

    linked_users = set(frappe.get_all("WAFD Driver", filters={"system_user": ["is", "set"]}, pluck="system_user"))
    eligible = [u for u in eligible if u not in linked_users]
    unlinked_drivers = frappe.get_all("WAFD Driver", filters={"system_user": ["is", "not set"]}, pluck="name")

    if len(eligible) == 1 and len(unlinked_drivers) == 1:
        frappe.db.set_value(
            "WAFD Driver",
            unlinked_drivers[0],
            "system_user",
            eligible[0],
            update_modified=False,
        )

    frappe.clear_cache(doctype="WAFD Driver")
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="WAFD Delivery Proof")
    frappe.clear_cache()
