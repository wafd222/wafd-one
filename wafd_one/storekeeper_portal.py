"""Small, role-scoped data service for the mobile storekeeper home."""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}


def _check_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("غير مصرح لك بفتح شاشة أمين المستودع / Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_cleaning_handover_options(warehouse=None):
    """Return only active cleaning warehouses, supervisors and available stock."""
    _check_access()
    warehouses = frappe.get_all(
        "WAFD Warehouse",
        filters={"warehouse_type": "نظافة / Cleaning", "status": "نشط / Active"},
        fields=["name", "warehouse_name"],
        order_by="warehouse_name asc",
    )
    supervisors = frappe.db.sql(
        """select distinct u.name, coalesce(nullif(u.full_name, ''), u.name) as full_name
             from `tabUser` u
             join `tabHas Role` r on r.parent=u.name and r.parenttype='User'
            where u.enabled=1 and r.role='WAFD Cleaning Supervisor'
            order by full_name asc""",
        as_dict=True,
    )
    items = []
    if warehouse:
        valid_warehouse = next((row.name for row in warehouses if row.name == warehouse), None)
        if not valid_warehouse:
            frappe.throw(_("اختر مستودع نظافة نشط / Select an active cleaning warehouse"))
        items = frappe.db.sql(
            """select i.name as ingredient, i.uom, i.category,
                      coalesce(b.available_quantity, 0) as available_quantity,
                      coalesce(b.average_cost, 0) as average_cost,
                      i.standard_cost, i.latest_market_cost
                 from `tabWAFD Ingredient` i
                 left join `tabWAFD Stock Balance` b
                   on b.ingredient=i.name and b.warehouse=%s
                where i.status='نشط / Active'
                  and (b.name is not null or i.preferred_warehouse=%s
                       or i.category in ('منظفات / Cleaning','تعقيم وسلامة / Hygiene & Safety'))
                order by (coalesce(b.available_quantity,0)>0) desc,
                         i.category asc, i.ingredient_name asc""",
            (warehouse, warehouse),
            as_dict=True,
        )
        for row in items:
            row["unit_cost"] = flt(row.average_cost) or flt(row.latest_market_cost) or flt(row.standard_cost)
            row["can_issue"] = 1 if flt(row.available_quantity) > 0 else 0
    return {"warehouses": warehouses, "supervisors": supervisors, "items": items}


@frappe.whitelist()
def create_cleaning_handover(source_warehouse, issued_to_user, items):
    """Create and post a cleaning handover from the simplified Storekeeper UI."""
    _check_access()
    warehouse = frappe.db.get_value(
        "WAFD Warehouse", source_warehouse, ["warehouse_type", "status"], as_dict=True
    )
    if not warehouse or warehouse.warehouse_type != "نظافة / Cleaning" or warehouse.status != "نشط / Active":
        frappe.throw(_("المستودع المختار ليس مستودع نظافة نشطاً / Invalid cleaning warehouse"))
    if not frappe.db.get_value("User", issued_to_user, "enabled") or "WAFD Cleaning Supervisor" not in frappe.get_roles(issued_to_user):
        frappe.throw(_("اختر مشرف نظافة نشطاً / Select an active Cleaning Supervisor"))

    rows = frappe.parse_json(items) if isinstance(items, str) else items
    if not isinstance(rows, list) or not rows:
        frappe.throw(_("اختر مادة واحدة على الأقل / Select at least one item"))
    seen = set()
    movement_items = []
    for row in rows:
        ingredient = (row.get("ingredient") or "").strip()
        quantity = flt(row.get("quantity"))
        unit_cost = flt(row.get("unit_cost"))
        if not ingredient or ingredient in seen:
            frappe.throw(_("قائمة المواد غير صالحة أو تحتوي تكراراً / Invalid or duplicate items"))
        seen.add(ingredient)
        balance = frappe.db.get_value(
            "WAFD Stock Balance",
            {"warehouse": source_warehouse, "ingredient": ingredient},
            ["available_quantity", "uom"],
            as_dict=True,
        )
        if not balance or quantity <= 0 or quantity > flt(balance.available_quantity) + 0.000001:
            frappe.throw(_(f"الكمية المطلوبة غير متاحة للمادة {ingredient} / Requested quantity is unavailable"))
        if unit_cost < 0:
            frappe.throw(_("سعر الوحدة لا يمكن أن يكون سالباً / Unit price cannot be negative"))
        movement_items.append({
            "ingredient": ingredient,
            "quantity": quantity,
            "uom": balance.uom,
            "unit_cost": unit_cost,
        })

    doc = frappe.get_doc({
        "doctype": "WAFD Stock Movement",
        "movement_type": "صرف / Issue",
        "posting_date": now_datetime(),
        "source_warehouse": source_warehouse,
        "issue_purpose": "نظافة / Cleaning",
        "issued_to_user": issued_to_user,
        "items": movement_items,
        "notes": "تم الإرسال من شاشة أمين المستودع المبسطة / Sent from simplified Storekeeper page",
    })
    doc.insert()
    from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import post_movement
    post_movement(doc.name)
    return {"name": doc.name, "handover_status": "بانتظار الاستلام / Pending Receipt"}


@frappe.whitelist()
def receive_cleaning_material(target_warehouse, ingredient, quantity, unit_cost=0):
    """Receive one cleaning item through a minimal audited Stock Movement."""
    _check_access()
    warehouse = frappe.db.get_value(
        "WAFD Warehouse", target_warehouse, ["warehouse_type", "status"], as_dict=True
    )
    if not warehouse or warehouse.warehouse_type != "نظافة / Cleaning" or warehouse.status != "نشط / Active":
        frappe.throw(_("المستودع المختار ليس مستودع نظافة نشطاً / Invalid cleaning warehouse"))
    item = frappe.db.get_value(
        "WAFD Ingredient", ingredient,
        ["status", "category", "preferred_warehouse", "uom"], as_dict=True,
    )
    if not item or item.status != "نشط / Active":
        frappe.throw(_("المادة غير نشطة أو غير موجودة / Item is missing or inactive"))
    if item.preferred_warehouse != target_warehouse and item.category not in (
        "منظفات / Cleaning", "تعقيم وسلامة / Hygiene & Safety"
    ):
        frappe.throw(_("المادة ليست من مواد مستودع النظافة / Item is not a cleaning-store item"))
    quantity = flt(quantity)
    unit_cost = flt(unit_cost)
    if quantity <= 0:
        frappe.throw(_("اكتب كمية استلام أكبر من صفر / Receipt quantity must be greater than zero"))
    if unit_cost < 0:
        frappe.throw(_("سعر الوحدة لا يمكن أن يكون سالباً / Unit price cannot be negative"))

    doc = frappe.get_doc({
        "doctype": "WAFD Stock Movement",
        "movement_type": "استلام / Receipt",
        "posting_date": now_datetime(),
        "target_warehouse": target_warehouse,
        "items": [{
            "ingredient": ingredient,
            "quantity": quantity,
            "uom": item.uom,
            "unit_cost": unit_cost,
        }],
        "notes": "استلام مبسط من شاشة إرسال مواد النظافة / Simplified cleaning-material receipt",
    })
    doc.insert()
    from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import post_movement
    post_movement(doc.name)
    return {"name": doc.name, "ingredient": ingredient, "quantity": quantity}


@frappe.whitelist()
def get_storekeeper_snapshot(warehouse=None, search=None):
    """Return a compact, read-only balance snapshot for the simplified page."""
    _check_access()

    warehouses = frappe.get_list(
        "WAFD Warehouse",
        filters={"status": "نشط / Active"},
        fields=["name", "warehouse_name", "warehouse_type"],
        order_by="warehouse_name asc",
        limit_page_length=100,
    )

    filters = {}
    if warehouse:
        filters["warehouse"] = warehouse
    or_filters = None
    cleaned_search = (search or "").strip()
    if cleaned_search:
        like = f"%{cleaned_search}%"
        or_filters = {"ingredient": ["like", like], "warehouse": ["like", like]}

    balance_args = {
        "filters": filters,
        "fields": [
            "name", "warehouse", "ingredient", "uom", "actual_quantity",
            "reserved_quantity", "available_quantity", "last_movement_date",
        ],
        "order_by": "warehouse asc, ingredient asc",
        "limit_page_length": 1000,
    }
    if or_filters:
        balance_args["or_filters"] = or_filters
    balances = frappe.get_list("WAFD Stock Balance", **balance_args)

    pending_orders = frappe.get_list(
        "WAFD Purchase Order",
        filters={"status": ["in", ["معتمد / Approved", "مرسل / Sent", "مستلم جزئياً / Partially Received"]]},
        fields=["name"],
        limit_page_length=500,
    )
    handovers = frappe.get_all(
        "WAFD Stock Movement",
        filters={
            "movement_type": "صرف / Issue",
            "issue_purpose": "نظافة / Cleaning",
            "handover_status": ["!=", "غير مرسل / Not Sent"],
            "is_pre_go_live_test": 0,
        },
        fields=["name", "posting_date", "issued_to_user", "handover_status", "handover_sent_on", "handover_received_on", "handover_rejection_reason"],
        order_by="posting_date desc",
        limit_page_length=20,
    )
    for handover in handovers:
        handover["items"] = frappe.get_all(
            "WAFD Stock Movement Item", filters={"parent": handover.name},
            fields=["ingredient", "quantity", "uom"], order_by="idx asc",
        )
        usage_names = frappe.get_all(
            "WAFD Cleaning Material Usage", filters={"source_handover": handover.name},
            fields=["name", "usage_date", "purpose", "location"], order_by="usage_date desc",
        )
        for usage in usage_names:
            usage["items"] = frappe.get_all(
                "WAFD Cleaning Material Usage Item", filters={"parent": usage.name},
                fields=["ingredient", "quantity", "uom"], order_by="idx asc",
            )
        handover["usage"] = usage_names
    return {
        "warehouses": warehouses,
        "balances": balances,
        "pending_purchase_orders": len(pending_orders),
        "cleaning_handovers": handovers,
    }
