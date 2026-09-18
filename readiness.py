import frappe
from wafd_one import __version__

CORE_DOCTYPES = (
    "WAFD Contract", "WAFD Catering Project", "WAFD Daily Meal Plan",
    "WAFD Production Batch", "WAFD Quality Inspection", "WAFD Packaging Record",
    "WAFD Loading Record", "WAFD Delivery Trip", "WAFD Delivery Proof",
    "WAFD Invoice", "WAFD Payment", "WAFD Kitchen", "WAFD Warehouse",
)


def _count(doctype):
    return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def _active_kitchens():
    if not frappe.db.exists("DocType", "WAFD Kitchen"):
        return 0
    meta = frappe.get_meta("WAFD Kitchen")
    if meta.has_field("status"):
        return frappe.db.count("WAFD Kitchen", {"status": "نشط / Active"})
    if meta.has_field("is_active"):
        return frappe.db.count("WAFD Kitchen", {"is_active": 1})
    return frappe.db.count("WAFD Kitchen")


@frappe.whitelist()
def get_release_readiness():
    missing = [name for name in CORE_DOCTYPES if not frappe.db.exists("DocType", name)]
    kitchens = _active_kitchens()
    warehouses = _count("WAFD Warehouse")
    recipes = _count("WAFD Recipe")
    hotels = _count("WAFD Hotel")
    missions = _count("WAFD Mission")
    checks = [
        {"label": "النماذج التشغيلية", "ok": not missing, "detail": "جميع النماذج الأساسية مثبتة" if not missing else "مفقود: " + ", ".join(missing)},
        {"label": "المطبخ المسؤول", "ok": kitchens > 0, "detail": f"عدد المطابخ النشطة: {kitchens}"},
        {"label": "المستودعات والثلاجات", "ok": warehouses > 0, "detail": f"عدد السجلات: {warehouses}"},
        {"label": "الوصفات", "ok": recipes > 0, "detail": f"عدد الوصفات: {recipes}"},
        {"label": "الفنادق", "ok": hotels > 0, "detail": f"عدد الفنادق: {hotels}"},
        {"label": "البعثات والعملاء", "ok": missions > 0, "detail": f"عدد السجلات: {missions}"},
    ]
    return {
        "version": __version__,
        "ready": all(row["ok"] for row in checks),
        "checks": checks,
        "counts": {
            "contracts": _count("WAFD Contract"),
            "projects": _count("WAFD Catering Project"),
            "daily_plans": _count("WAFD Daily Meal Plan"),
            "production_batches": _count("WAFD Production Batch"),
            "deliveries": _count("WAFD Delivery Proof"),
            "invoices": _count("WAFD Invoice"),
        },
    }
