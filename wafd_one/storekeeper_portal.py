"""Small, role-scoped data service for the mobile storekeeper home."""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}

RECIPIENT_ROLES = {
    "WAFD Cleaning Supervisor": "مشرف النظافة",
    "WAFD Production Supervisor": "مشرف الطبخ / الشيف / مشرف الإنتاج",
    "WAFD Project Manager": "مدير المشروع",
    "WAFD Quality Inspector": "مفتش الجودة",
    "WAFD Delivery Supervisor": "مشرف التوصيل",
}


def _check_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("غير مصرح لك بفتح شاشة أمين المستودع / Not permitted"), frappe.PermissionError)


def _active_warehouses():
    return frappe.get_all(
        "WAFD Warehouse",
        filters={"status": "نشط / Active"},
        fields=["name", "warehouse_name", "warehouse_type"],
        order_by="warehouse_type asc, warehouse_name asc",
        limit_page_length=200,
    )


def _active_recipients():
    role_names = tuple(RECIPIENT_ROLES)
    placeholders = ", ".join(["%s"] * len(role_names))
    rows = frappe.db.sql(
        f"""select distinct r.role, u.name,
                    coalesce(nullif(u.full_name, ''),
                             nullif(trim(concat_ws(' ', u.first_name, u.last_name)), ''),
                             u.name) as full_name
               from `tabUser` u
               join `tabHas Role` r on r.parent=u.name and r.parenttype='User'
              where u.enabled=1 and r.role in ({placeholders})
              order by r.role asc, full_name asc""",
        role_names,
        as_dict=True,
    )
    for row in rows:
        row["role_label"] = RECIPIENT_ROLES.get(row.role, row.role)
    return rows


def _parse_rows(items):
    rows = frappe.parse_json(items) if isinstance(items, str) else items
    if not isinstance(rows, list) or not rows:
        frappe.throw(_("اختر مادة واحدة على الأقل / Select at least one item"))
    return rows


def _post(doc):
    doc.insert()
    from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import post_movement
    post_movement(doc.name)
    return doc


@frappe.whitelist()
def get_storekeeper_workflow_options(warehouse=None, search=None, category=None, receipt=0):
    """Return small searchable lists for the three practical Storekeeper flows."""
    _check_access()
    warehouses = _active_warehouses()
    valid_names = {row.name for row in warehouses}
    if warehouse and warehouse not in valid_names:
        frappe.throw(_("اختر مستودعاً نشطاً / Select an active warehouse"))

    conditions = ["i.status='نشط / Active'"]
    values = []
    if category:
        conditions.append("i.category=%s")
        values.append(category)
    cleaned_search = (search or "").strip()
    if cleaned_search:
        like = f"%{cleaned_search}%"
        conditions.append("(i.ingredient_name like %s or i.item_code like %s or i.category like %s)")
        values.extend([like, like, like])

    if warehouse and not int(receipt or 0):
        conditions.append("b.warehouse=%s and coalesce(b.available_quantity,0)>0")
        values.append(warehouse)
        join = "join `tabWAFD Stock Balance` b on b.ingredient=i.name"
    else:
        join = "left join `tabWAFD Stock Balance` b on b.ingredient=i.name and b.warehouse=%s" if warehouse else "left join `tabWAFD Stock Balance` b on 1=0"
        if warehouse:
            values.insert(0, warehouse)

    items = frappe.db.sql(
        f"""select i.name as ingredient, i.item_code, i.category, i.uom,
                    coalesce(b.available_quantity,0) as available_quantity,
                    coalesce(b.average_cost,0) as average_cost,
                    i.standard_cost, i.latest_market_cost, i.minimum_stock
               from `tabWAFD Ingredient` i
               {join}
              where {' and '.join(conditions)}
              order by i.category asc, i.ingredient_name asc
              limit 80""",
        tuple(values),
        as_dict=True,
    )
    for row in items:
        row["unit_cost"] = flt(row.average_cost) or flt(row.latest_market_cost) or flt(row.standard_cost)
    categories = frappe.db.sql(
        """select distinct category from `tabWAFD Ingredient`
            where status='نشط / Active' and coalesce(category,'')!=''
            order by category asc""",
        as_dict=True,
    )
    return {
        "warehouses": warehouses,
        "recipients": _active_recipients(),
        "categories": [row.category for row in categories if row.category],
        "items": items,
    }


@frappe.whitelist()
def receive_inventory_materials(target_warehouse, items):
    """Post a multi-item receipt without exposing the technical movement form."""
    _check_access()
    warehouse = frappe.db.get_value("WAFD Warehouse", target_warehouse, ["status"], as_dict=True)
    if not warehouse or warehouse.status != "نشط / Active":
        frappe.throw(_("اختر مستودعاً أو ثلاجة نشطة / Select an active warehouse or fridge"))
    movement_items = []
    seen = set()
    for row in _parse_rows(items):
        ingredient = (row.get("ingredient") or "").strip()
        quantity = flt(row.get("quantity"))
        unit_cost = flt(row.get("unit_cost"))
        item = frappe.db.get_value("WAFD Ingredient", ingredient, ["status", "uom"], as_dict=True)
        if not item or item.status != "نشط / Active" or ingredient in seen:
            frappe.throw(_("قائمة المواد غير صالحة أو تحتوي تكراراً / Invalid or duplicate items"))
        if quantity <= 0:
            frappe.throw(_(f"اكتب كمية صحيحة للمادة {ingredient} / Enter a valid quantity"))
        if unit_cost < 0:
            frappe.throw(_("سعر الوحدة لا يمكن أن يكون سالباً / Unit price cannot be negative"))
        seen.add(ingredient)
        movement_items.append({
            "ingredient": ingredient, "quantity": quantity, "uom": item.uom,
            "unit_cost": unit_cost, "expiry_date": row.get("expiry_date") or None,
        })
    doc = frappe.get_doc({
        "doctype": "WAFD Stock Movement", "movement_type": "استلام / Receipt",
        "posting_date": now_datetime(), "target_warehouse": target_warehouse,
        "items": movement_items,
        "notes": "استلام وتوزيع من شاشة أمين المستودع العملية / Practical Storekeeper receipt",
    })
    _post(doc)
    return {"name": doc.name, "items_count": len(movement_items), "warehouse": target_warehouse}


@frappe.whitelist()
def create_employee_handover(source_warehouse, issued_to_user, recipient_role, items):
    """Issue available materials to a named employee selected by operational role."""
    _check_access()
    if recipient_role not in RECIPIENT_ROLES:
        frappe.throw(_("اختر وظيفة مستلم صحيحة / Select a valid recipient role"))
    if not frappe.db.get_value("User", issued_to_user, "enabled") or recipient_role not in frappe.get_roles(issued_to_user):
        frappe.throw(_("الموظف غير نشط أو لا يحمل الوظيفة المختارة / Invalid employee for the selected role"))
    warehouse = frappe.db.get_value("WAFD Warehouse", source_warehouse, ["warehouse_type", "status"], as_dict=True)
    if not warehouse or warehouse.status != "نشط / Active":
        frappe.throw(_("اختر مستودعاً أو ثلاجة نشطة / Select an active warehouse or fridge"))
    if warehouse.warehouse_type == "نظافة / Cleaning" and recipient_role != "WAFD Cleaning Supervisor":
        frappe.throw(_("مواد مستودع النظافة تسلّم لمشرف النظافة / Cleaning stock must go to a Cleaning Supervisor"))

    movement_items = []
    seen = set()
    for row in _parse_rows(items):
        ingredient = (row.get("ingredient") or "").strip()
        quantity = flt(row.get("quantity"))
        unit_cost = flt(row.get("unit_cost"))
        if not ingredient or ingredient in seen:
            frappe.throw(_("قائمة المواد غير صالحة أو تحتوي تكراراً / Invalid or duplicate items"))
        seen.add(ingredient)
        balance = frappe.db.get_value(
            "WAFD Stock Balance", {"warehouse": source_warehouse, "ingredient": ingredient},
            ["available_quantity", "uom"], as_dict=True,
        )
        if not balance or quantity <= 0 or quantity > flt(balance.available_quantity) + 0.000001:
            frappe.throw(_(f"الكمية المطلوبة غير متاحة للمادة {ingredient} / Requested quantity is unavailable"))
        if unit_cost < 0:
            frappe.throw(_("سعر الوحدة لا يمكن أن يكون سالباً / Unit price cannot be negative"))
        movement_items.append({"ingredient": ingredient, "quantity": quantity, "uom": balance.uom, "unit_cost": unit_cost})

    purpose = "نظافة / Cleaning" if recipient_role == "WAFD Cleaning Supervisor" else "تشغيل / Operations"
    doc = frappe.get_doc({
        "doctype": "WAFD Stock Movement", "movement_type": "صرف / Issue",
        "posting_date": now_datetime(), "source_warehouse": source_warehouse,
        "issue_purpose": purpose, "issued_to_user": issued_to_user,
        "items": movement_items,
        "notes": f"تسليم مبسط إلى {RECIPIENT_ROLES[recipient_role]} / Practical employee handover",
    })
    _post(doc)
    full_name = frappe.db.get_value("User", issued_to_user, "full_name") or issued_to_user
    return {
        "name": doc.name, "recipient": full_name, "items_count": len(movement_items),
        "handover_status": doc.get("handover_status"),
    }


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
    """Return balances, shortages and expiry alerts for the information screen."""
    _check_access()
    warehouses = _active_warehouses()
    valid_names = {row.name for row in warehouses}
    if warehouse and warehouse not in valid_names:
        frappe.throw(_("اختر مستودعاً نشطاً / Select an active warehouse"))

    conditions = ["1=1"]
    values = []
    if warehouse:
        conditions.append("b.warehouse=%s")
        values.append(warehouse)
    cleaned_search = (search or "").strip()
    if cleaned_search:
        like = f"%{cleaned_search}%"
        conditions.append("(b.ingredient like %s or b.warehouse like %s or i.category like %s)")
        values.extend([like, like, like])
    balances = frappe.db.sql(
        f"""select b.name, b.warehouse, b.ingredient, b.uom, b.actual_quantity,
                    b.reserved_quantity, b.available_quantity, b.average_cost,
                    b.last_movement_date, i.category, coalesce(i.minimum_stock,0) as minimum_stock
               from `tabWAFD Stock Balance` b
               left join `tabWAFD Ingredient` i on i.name=b.ingredient
              where {' and '.join(conditions)}
              order by b.warehouse asc, b.ingredient asc
              limit 1000""",
        tuple(values), as_dict=True,
    )
    for row in balances:
        available = flt(row.available_quantity)
        minimum = flt(row.minimum_stock)
        row["is_zero"] = 1 if available <= 0 else 0
        row["is_low"] = 1 if minimum > 0 and available <= minimum else 0

    expiry_conditions = [
        "sm.status='مرحلة / Posted'", "sm.movement_type='استلام / Receipt'",
        "coalesce(sm.is_pre_go_live_test,0)=0", "mi.expiry_date is not null",
        "b.available_quantity>0", "mi.expiry_date<=date_add(curdate(), interval 30 day)",
    ]
    expiry_values = []
    if warehouse:
        expiry_conditions.append("sm.target_warehouse=%s")
        expiry_values.append(warehouse)
    if cleaned_search:
        like = f"%{cleaned_search}%"
        expiry_conditions.append("(mi.ingredient like %s or sm.target_warehouse like %s)")
        expiry_values.extend([like, like])
    expiry_alerts = frappe.db.sql(
        f"""select sm.name as movement, sm.target_warehouse as warehouse,
                    mi.ingredient, mi.expiry_date, mi.quantity, mi.uom,
                    datediff(mi.expiry_date, curdate()) as days_remaining
               from `tabWAFD Stock Movement` sm
               join `tabWAFD Stock Movement Item` mi on mi.parent=sm.name
               join `tabWAFD Stock Balance` b
                 on b.warehouse=sm.target_warehouse and b.ingredient=mi.ingredient
              where {' and '.join(expiry_conditions)}
              order by mi.expiry_date asc
              limit 200""",
        tuple(expiry_values), as_dict=True,
    )

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
        handover["issued_to_name"] = frappe.db.get_value("User", handover.issued_to_user, "full_name") or handover.issued_to_user
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
        "expiry_alerts": expiry_alerts,
        "summary": {
            "warehouses": len(warehouses),
            "materials": len(balances),
            "low": sum(1 for row in balances if row.is_low),
            "zero": sum(1 for row in balances if row.is_zero),
            "expiring": sum(1 for row in expiry_alerts if row.days_remaining >= 0),
            "expired": sum(1 for row in expiry_alerts if row.days_remaining < 0),
        },
        "pending_purchase_orders": len(pending_orders),
        "cleaning_handovers": handovers,
    }
