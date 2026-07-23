import frappe

CORE_DOCTYPES = (
    "WAFD Contract", "WAFD Catering Project", "WAFD Daily Meal Plan",
    "WAFD Production Batch", "WAFD Quality Inspection", "WAFD Packaging Record",
    "WAFD Loading Record", "WAFD Delivery Trip", "WAFD Delivery Proof",
    "WAFD Invoice", "WAFD Payment", "WAFD Kitchen", "WAFD Warehouse",
)

@frappe.whitelist()
def get_release_readiness():
    missing = [name for name in CORE_DOCTYPES if not frappe.db.exists("DocType", name)]
    checks = [
        {"label": "Core metadata", "ok": not missing, "detail": ", ".join(missing) if missing else "All operational DocTypes are installed"},
        {"label": "Main kitchen", "ok": bool(frappe.db.exists("WAFD Kitchen", {"is_active": 1})), "detail": "At least one active kitchen is required"},
        {"label": "Warehouses", "ok": frappe.db.count("WAFD Warehouse") > 0, "detail": f"{frappe.db.count('WAFD Warehouse')} warehouse records"},
        {"label": "Recipes", "ok": frappe.db.count("WAFD Recipe") > 0, "detail": f"{frappe.db.count('WAFD Recipe')} recipes"},
        {"label": "Hotels", "ok": frappe.db.count("WAFD Hotel") > 0, "detail": f"{frappe.db.count('WAFD Hotel')} hotels"},
        {"label": "Missions", "ok": frappe.db.count("WAFD Mission") > 0, "detail": f"{frappe.db.count('WAFD Mission')} missions/clients"},
    ]
    return {
        "version": "10.0.0 RC1",
        "ready": all(row["ok"] for row in checks),
        "checks": checks,
        "counts": {
            "contracts": frappe.db.count("WAFD Contract"),
            "projects": frappe.db.count("WAFD Catering Project"),
            "daily_plans": frappe.db.count("WAFD Daily Meal Plan"),
            "production_batches": frappe.db.count("WAFD Production Batch"),
            "deliveries": frappe.db.count("WAFD Delivery Proof"),
            "invoices": frappe.db.count("WAFD Invoice"),
        },
    }
