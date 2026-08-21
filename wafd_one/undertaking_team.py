import frappe
from frappe import _

OFFICER = "WAFD Undertaking Officer"
MANAGERS = {"System Manager", "WAFD Operations Manager"}


def _assert_manager():
    if not (set(frappe.get_roles(frappe.session.user)) & MANAGERS):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def list_officers():
    _assert_manager()
    users = frappe.get_all(
        "Has Role", filters={"role": OFFICER, "parenttype": "User"}, pluck="parent"
    )
    if not users:
        return []
    rows = frappe.get_all(
        "User", filters={"name": ["in", users]},
        fields=["name", "full_name", "email", "enabled", "last_login"], order_by="full_name asc"
    )
    return rows


@frappe.whitelist()
def create_officer(email, first_name, password=None):
    _assert_manager()
    email = (email or "").strip().lower()
    first_name = (first_name or "").strip()
    if not email or "@" not in email:
        frappe.throw(_("Enter a valid, unique employee email address."))
    if not first_name:
        frappe.throw(_("Employee name is required."))
    if frappe.db.exists("User", email):
        frappe.throw(_("A user already exists with this email address."))

    user = frappe.get_doc({
        "doctype": "User", "email": email, "first_name": first_name,
        "enabled": 1, "send_welcome_email": 0, "user_type": "System User",
        "roles": [{"role": OFFICER}],
    })
    user.flags.ignore_permissions = True
    user.insert()
    if password:
        from frappe.utils.password import update_password
        update_password(email, password, logout_all_sessions=True)
    return {"name": user.name, "full_name": user.full_name, "email": user.email, "enabled": user.enabled}


@frappe.whitelist()
def set_officer_enabled(user, enabled=1):
    _assert_manager()
    if not frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": OFFICER}):
        frappe.throw(_("This user is not an undertaking officer."))
    if user == frappe.session.user:
        frappe.throw(_("You cannot disable your own active account here."))
    frappe.db.set_value("User", user, "enabled", 1 if int(enabled) else 0)
    frappe.clear_cache(user=user)
    return True
