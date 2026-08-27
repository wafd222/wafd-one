"""Manager-only WAFD employee account and operational-role administration."""

import re

import frappe
from frappe import _
from frappe.utils import cint, validate_email_address


MANAGERS = {"System Manager", "WAFD Operations Manager"}

# Deliberately excludes management roles. This page must never be usable as a
# privilege-escalation path to System Manager or WAFD Operations Manager.
ROLE_LABELS = {
    "WAFD Project Manager": "مدير مشروع",
    "WAFD Production Supervisor": "مشرف الإنتاج",
    "WAFD Quality Inspector": "مفتش الجودة",
    "WAFD Storekeeper": "أمين المستودع",
    "WAFD Cleaning Supervisor": "مشرف النظافة",
    "WAFD Delivery Supervisor": "مشرف التوصيل",
    "WAFD Driver": "سائق",
    "WAFD Finance User": "موظف المالية",
    "WAFD Approver": "المعتمد",
    "WAFD Auditor": "المدقق",
    "WAFD Undertaking Officer": "مسؤول التعهدات",
    "WAFD Undertaking Reviewer": "مراجع التعهدات",
}
ROLE_LABELS_EN = {
    "WAFD Project Manager": "Project Manager",
    "WAFD Production Supervisor": "Production Supervisor",
    "WAFD Quality Inspector": "Quality Inspector",
    "WAFD Storekeeper": "Storekeeper",
    "WAFD Cleaning Supervisor": "Cleaning Supervisor",
    "WAFD Delivery Supervisor": "Delivery Supervisor",
    "WAFD Driver": "Driver",
    "WAFD Finance User": "Finance User",
    "WAFD Approver": "Approver",
    "WAFD Auditor": "Auditor",
    "WAFD Undertaking Officer": "Undertaking Officer",
    "WAFD Undertaking Reviewer": "Undertaking Reviewer",
}
MANAGED_ROLES = tuple(ROLE_LABELS)
DRIVER_ROLE = "WAFD Driver"


def _assert_manager():
    if not (set(frappe.get_roles(frappe.session.user)) & MANAGERS):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def _normalize_email(email):
    email = (email or "").strip().lower()
    if not email or not validate_email_address(email):
        frappe.throw(_("Enter a valid, unique employee email address."))
    return email


def _normalize_mobile(mobile, required=False):
    """Accept Saudi local/international mobile formats and store E.164."""
    value = str(mobile or "").strip().translate(
        str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    )
    if not value:
        if required:
            frappe.throw(_("رقم الجوال مطلوب عند اختيار مهمة سائق."))
        return ""

    value = re.sub(r"[\s\-().]", "", value)
    if value.startswith("00"):
        value = f"+{value[2:]}"
    elif re.fullmatch(r"05\d{8}", value):
        value = f"+966{value[1:]}"
    elif re.fullmatch(r"9665\d{8}", value):
        value = f"+{value}"

    if not re.fullmatch(r"\+[1-9]\d{7,14}", value):
        frappe.throw(_("أدخل رقم جوال صحيحًا بصيغة 05xxxxxxxx أو +9665xxxxxxxx."))
    return value


def _validate_role(role):
    role = (role or "").strip()
    if role not in ROLE_LABELS:
        frappe.throw(_("Select a valid WAFD employee task."))
    if not frappe.db.exists("Role", role):
        frappe.throw(_("The selected WAFD role is not installed."))
    return role


def _user_roles(user):
    return {
        row.role
        for row in frappe.get_all(
            "Has Role",
            filters={"parent": user, "parenttype": "User"},
            fields=["role"],
        )
    }


def _assert_manageable_user(user):
    if not user or user in {"Administrator", "Guest", frappe.session.user}:
        frappe.throw(_("This account cannot be changed from employee management."))
    if not frappe.db.exists("User", user):
        frappe.throw(_("Employee account was not found."))
    if _user_roles(user) & MANAGERS:
        frappe.throw(_("Management accounts cannot be changed from employee management."))


def _managed_role_rows(user_doc):
    return [row for row in user_doc.roles if row.role in MANAGED_ROLES]


def _set_driver_status(user, status):
    if not frappe.db.exists("DocType", "WAFD Driver"):
        return
    driver = frappe.db.get_value("WAFD Driver", {"system_user": user}, "name")
    if driver:
        frappe.db.set_value("WAFD Driver", driver, "status", status)


def _ensure_driver_profile(user, full_name, mobile):
    if not frappe.db.exists("DocType", "WAFD Driver"):
        return
    mobile = _normalize_mobile(mobile, required=True)

    existing = frappe.db.get_value("WAFD Driver", {"system_user": user}, "name")
    if existing:
        driver = frappe.get_doc("WAFD Driver", existing)
        driver.mobile = mobile
        driver.status = "متاح / Available"
        driver.flags.ignore_permissions = True
        driver.save()
        return

    unlinked = frappe.db.get_value(
        "WAFD Driver", {"driver_name": full_name, "system_user": ["is", "not set"]}, "name"
    )
    if unlinked:
        driver = frappe.get_doc("WAFD Driver", unlinked)
        driver.system_user = user
        driver.mobile = mobile
        driver.status = "متاح / Available"
        driver.flags.ignore_permissions = True
        driver.save()
        return

    driver_name = full_name
    if frappe.db.exists("WAFD Driver", driver_name):
        driver_name = f"{full_name} - {user.split('@', 1)[0]}"
    driver = frappe.get_doc(
        {
            "doctype": "WAFD Driver",
            "driver_name": driver_name,
            "system_user": user,
            "mobile": mobile,
            "status": "متاح / Available",
        }
    )
    driver.flags.ignore_permissions = True
    driver.insert()


def _role_options():
    return [
        {"role": role, "label": label, "label_en": ROLE_LABELS_EN[role]}
        for role, label in ROLE_LABELS.items()
        if frappe.db.exists("Role", role)
    ]


@frappe.whitelist()
def list_employees():
    _assert_manager()
    assignments = frappe.get_all(
        "Has Role",
        filters={"role": ["in", MANAGED_ROLES], "parenttype": "User"},
        fields=["parent", "role"],
        order_by="parent asc",
    )
    user_names = sorted({row.parent for row in assignments} - {"Administrator", "Guest"})
    if not user_names:
        return {"employees": [], "roles": _role_options()}

    manager_users = set(
        frappe.get_all(
            "Has Role",
            filters={"parent": ["in", user_names], "parenttype": "User", "role": ["in", tuple(MANAGERS)]},
            pluck="parent",
        )
    )
    user_names = [name for name in user_names if name not in manager_users]
    if not user_names:
        return {"employees": [], "roles": _role_options()}

    role_map = {name: [] for name in user_names}
    for row in assignments:
        if row.parent in role_map and row.role not in role_map[row.parent]:
            role_map[row.parent].append(row.role)

    users = frappe.get_all(
        "User",
        filters={"name": ["in", user_names], "user_type": "System User"},
        fields=["name", "full_name", "email", "mobile_no", "enabled", "last_login"],
        order_by="full_name asc",
    )
    employees = []
    for user in users:
        roles = sorted(role_map.get(user.name) or [], key=MANAGED_ROLES.index)
        employees.append(
            {
                **user,
                "roles": roles,
                "role": roles[0] if len(roles) == 1 else "",
                "role_labels": [ROLE_LABELS[role] for role in roles],
            }
        )
    return {"employees": employees, "roles": _role_options()}


@frappe.whitelist()
def create_employee(email, first_name, role, password, mobile=None):
    _assert_manager()
    email = _normalize_email(email)
    first_name = (first_name or "").strip()
    role = _validate_role(role)
    password = password or ""
    mobile = _normalize_mobile(mobile, required=role == DRIVER_ROLE)

    if not first_name:
        frappe.throw(_("Employee name is required."))
    if len(password) < 8:
        frappe.throw(_("Temporary password must contain at least 8 characters."))
    if frappe.db.exists("User", email):
        frappe.throw(_("A user already exists with this email address."))

    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "mobile_no": mobile,
            "enabled": 1,
            "send_welcome_email": 0,
            "user_type": "System User",
            "roles": [{"role": role}],
        }
    )
    user.flags.ignore_permissions = True
    user.insert()

    from frappe.utils.password import update_password

    update_password(email, password, logout_all_sessions=True)
    if role == DRIVER_ROLE:
        _ensure_driver_profile(email, user.full_name or first_name, mobile)
    frappe.clear_cache(user=email)
    return {
        "name": user.name,
        "full_name": user.full_name,
        "email": user.email,
        "enabled": user.enabled,
        "role": role,
        "role_label": ROLE_LABELS[role],
    }


@frappe.whitelist()
def set_employee_enabled(user, enabled=1):
    _assert_manager()
    _assert_manageable_user(user)
    roles = _user_roles(user) & set(MANAGED_ROLES)
    if not roles:
        frappe.throw(_("This user is not a managed WAFD employee."))

    target_enabled = 1 if cint(enabled) else 0
    employee = frappe.get_doc("User", user)
    employee.enabled = target_enabled
    employee.flags.ignore_permissions = True
    employee.save()

    if DRIVER_ROLE in roles:
        _set_driver_status(user, "متاح / Available" if target_enabled else "غير نشط / Inactive")
    if not target_enabled:
        from frappe.sessions import clear_sessions

        clear_sessions(user=user, keep_current=False, force=True)
    frappe.clear_cache(user=user)
    return {"user": user, "enabled": target_enabled}


@frappe.whitelist()
def set_employee_role(user, role, mobile=None):
    _assert_manager()
    _assert_manageable_user(user)
    role = _validate_role(role)
    employee = frappe.get_doc("User", user)
    current_roles = {row.role for row in _managed_role_rows(employee)}
    if not current_roles:
        frappe.throw(_("This user is not a managed WAFD employee."))

    mobile = _normalize_mobile(mobile or employee.mobile_no, required=role == DRIVER_ROLE)

    employee.role_profile_name = None
    employee.set("roles", [{"role": row.role} for row in employee.roles if row.role not in MANAGED_ROLES])
    employee.append("roles", {"role": role})
    if mobile:
        employee.mobile_no = mobile
    employee.flags.ignore_permissions = True
    employee.save()

    if DRIVER_ROLE in current_roles and role != DRIVER_ROLE:
        _set_driver_status(user, "غير نشط / Inactive")
    if role == DRIVER_ROLE:
        _ensure_driver_profile(user, employee.full_name or employee.first_name, mobile)
    frappe.clear_cache(user=user)
    return {"user": user, "role": role, "role_label": ROLE_LABELS[role]}
