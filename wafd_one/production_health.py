import importlib
from pathlib import Path

import frappe

from wafd_one.setup import ALL_DOCTYPE_FILES, ROLES


def _check_permission():
    roles = set(frappe.get_roles())
    if not ({"System Manager", "WAFD Operations Manager"} & roles):
        frappe.throw("Not permitted", frappe.PermissionError)


def _patch_modules():
    patches_file = Path(__file__).resolve().parent / "patches.txt"
    modules = []
    section = None
    for raw in patches_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line
            continue
        modules.append((section, line))
    return modules


def run_health_check():
    missing_doctypes = [
        name.replace("_", " ").title().replace("Wafd", "WAFD")
        for name in ALL_DOCTYPE_FILES
        if not frappe.db.exists(
            "DocType", name.replace("_", " ").title().replace("Wafd", "WAFD")
        )
    ]

    missing_roles = [role for role in ROLES if not frappe.db.exists("Role", role)]
    patch_errors = []
    for section, module_name in _patch_modules():
        try:
            module = importlib.import_module(module_name)
            if not callable(getattr(module, "execute", None)):
                patch_errors.append({"patch": module_name, "error": "execute() is missing"})
        except Exception as exc:
            patch_errors.append({"patch": module_name, "error": str(exc)})

    workspace_ok = frappe.db.exists("Workspace", "WAFD ONE")
    page_ok = frappe.db.exists("Page", "wafd-administration-console")

    checks = {
        "missing_doctypes": missing_doctypes,
        "missing_roles": missing_roles,
        "patch_errors": patch_errors,
        "workspace_ok": bool(workspace_ok),
        "administration_page_ok": bool(page_ok),
    }
    checks["ok"] = not missing_doctypes and not missing_roles and not patch_errors and bool(workspace_ok) and bool(page_ok)
    return checks


@frappe.whitelist()
def production_health_check():
    _check_permission()
    return run_health_check()
