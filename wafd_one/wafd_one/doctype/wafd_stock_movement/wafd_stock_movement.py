import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, now_datetime, getdate

from wafd_one.uom import canonical_uom, uom_matches


class WAFDStockMovement(Document):
    def validate(self):
        if self.get("is_pre_go_live_test") and not self.is_new():
            frappe.throw("هذه حركة اختبار مؤرشفة قبل التشغيل الفعلي ولا يمكن تعديلها أو ترحيلها / Archived pre-Go-Live test movements cannot be edited or posted")
        if self.status == "مرحلة / Posted" and not self.posted_on:
            frappe.throw("استخدم زر ترحيل الحركة / Use the Post Movement button")
        total = 0
        for row in self.items or []:
            if flt(row.quantity) <= 0:
                frappe.throw("كمية الصنف يجب أن تكون أكبر من صفر / Item quantity must be greater than zero")
            row.amount = flt(row.quantity) * flt(row.unit_cost)
            total += row.amount
        self.total_amount = total
        self._validate_warehouses()
        self._validate_issue_recipient()
        self._validate_reference()
        self._validate_master_data()
        if self.posting_date and get_datetime(self.posting_date) > now_datetime():
            frappe.throw("تاريخ الترحيل لا يمكن أن يكون مستقبلياً / Posting date cannot be in the future")

    def _validate_master_data(self):
        seen = set()
        for row in self.items or []:
            if row.ingredient in seen:
                frappe.throw(f"المكون مكرر في الحركة: {row.ingredient} / Duplicate ingredient in movement")
            seen.add(row.ingredient)
            if flt(row.unit_cost) < 0:
                frappe.throw("تكلفة الوحدة لا يمكن أن تكون سالبة / Unit cost cannot be negative")
            ingredient = frappe.db.get_value("WAFD Ingredient", row.ingredient, ["status", "uom"], as_dict=True)
            if not ingredient or ingredient.status == "غير نشط / Inactive":
                frappe.throw(f"المكون غير نشط: {row.ingredient} / Ingredient is inactive")
            if row.uom and ingredient.uom and not uom_matches(row.uom, ingredient.uom):
                frappe.throw(f"وحدة الصنف {row.ingredient} يجب أن تكون {ingredient.uom} / Ingredient UOM mismatch")
            # Always persist the ingredient master UOM. This also repairs legacy
            # values such as ``Kg`` versus ``كجم / Kg`` without changing quantity.
            row.uom = canonical_uom(ingredient.uom or row.uom)
            if row.production_date and row.expiry_date and getdate(row.production_date) > getdate(row.expiry_date):
                frappe.throw(f"تاريخ إنتاج {row.ingredient} بعد تاريخ الانتهاء / Production date cannot be after expiry date")
            if self.movement_type == "استلام / Receipt" and row.expiry_date and getdate(row.expiry_date) <= getdate(self.posting_date):
                frappe.throw(f"لا يمكن استلام صنف منتهي أو ينتهي في تاريخ الاستلام: {row.ingredient} / Expired item cannot be received")
            if row.receiving_temperature is not None and (flt(row.receiving_temperature) < -50 or flt(row.receiving_temperature) > 100):
                frappe.throw(f"حرارة استلام غير منطقية للصنف {row.ingredient} / Invalid receiving temperature")


    def _validate_issue_recipient(self):
        if self.movement_type != "صرف / Issue":
            return
        if self.issued_to_user and not frappe.db.get_value("User", self.issued_to_user, "enabled"):
            frappe.throw("المستخدم المستلم غير نشط / Issued-to user is disabled")
        warehouse_type = frappe.db.get_value("WAFD Warehouse", self.source_warehouse, "warehouse_type") if self.source_warehouse else None
        if warehouse_type == "نظافة / Cleaning":
            self.issue_purpose = "نظافة / Cleaning"
            if not self.issued_to_user:
                frappe.throw("حدد مشرف النظافة المستلم قبل صرف مواد النظافة / Select the Cleaning Supervisor receiving the cleaning materials")
            if "WAFD Cleaning Supervisor" not in frappe.get_roles(self.issued_to_user):
                frappe.throw("مواد مستودع النظافة يجب صرفها لمستخدم بدور WAFD Cleaning Supervisor / Cleaning-store issues must be assigned to a Cleaning Supervisor")

    def _validate_reference(self):
        if self.reference_type == "WAFD Purchase Order" and self.reference_name:
            po = frappe.get_doc("WAFD Purchase Order", self.reference_name)
            if self.movement_type != "استلام / Receipt":
                frappe.throw("مرجع أمر الشراء مسموح لحركات الاستلام فقط / Purchase order references are only allowed for receipts")
            if po.status == "ملغي / Cancelled":
                frappe.throw("أمر الشراء ملغي / Purchase order is cancelled")
            if self.target_warehouse != po.warehouse:
                frappe.throw("مستودع الاستلام يجب أن يطابق مستودع أمر الشراء / Receipt warehouse must match the purchase order")
            ordered = {row.ingredient: row for row in po.items or []}
            posted = _posted_purchase_receipts(po.name, exclude_movement=self.name)
            for row in self.items or []:
                if row.ingredient not in ordered:
                    frappe.throw(f"الصنف {row.ingredient} غير موجود في أمر الشراء / Item is not in the purchase order")
                po_row = ordered[row.ingredient]
                if row.uom and po_row.uom and not uom_matches(row.uom, po_row.uom):
                    frappe.throw(f"وحدة استلام {row.ingredient} لا تطابق أمر الشراء / Receipt UOM mismatch")
                remaining = flt(po_row.quantity) - flt(posted.get(row.ingredient, 0))
                if flt(row.quantity) > remaining + 0.000001:
                    frappe.throw(
                        f"كمية استلام {row.ingredient} تتجاوز المتبقي {remaining} / Receipt exceeds outstanding quantity"
                    )

    def before_save(self):
        if not self.is_new() and self.get_db_value("status") == "مرحلة / Posted":
            frappe.throw("لا يمكن تعديل حركة مخزون مرحلة / A posted stock movement cannot be edited")

    def before_delete(self):
        if self.status == "مرحلة / Posted":
            frappe.throw("لا يمكن حذف حركة مخزون مرحلة / A posted stock movement cannot be deleted")

    def _validate_warehouses(self):
        if self.movement_type in ("صرف / Issue", "تحويل / Transfer", "هالك / Waste") and not self.source_warehouse:
            frappe.throw("حدد المستودع المصدر / Select source warehouse")
        if self.movement_type in ("استلام / Receipt", "تحويل / Transfer") and not self.target_warehouse:
            frappe.throw("حدد المستودع المستهدف / Select target warehouse")
        if self.movement_type == "تحويل / Transfer" and self.source_warehouse == self.target_warehouse:
            frappe.throw("المستودع المصدر والمستهدف يجب أن يكونا مختلفين / Source and target warehouses must differ")


def _posted_purchase_receipts(purchase_order_name, exclude_movement=None):
    totals = {}
    filters = {
        "movement_type": "استلام / Receipt",
        "reference_type": "WAFD Purchase Order",
        "reference_name": purchase_order_name,
        "status": "مرحلة / Posted",
        "is_pre_go_live_test": 0,
    }
    movements = frappe.get_all("WAFD Stock Movement", filters=filters, pluck="name")
    for name in movements:
        if exclude_movement and name == exclude_movement:
            continue
        doc = frappe.get_doc("WAFD Stock Movement", name)
        for row in doc.items or []:
            totals[row.ingredient] = totals.get(row.ingredient, 0) + flt(row.quantity)
    return totals


def _get_balance(warehouse, ingredient, uom=None, for_update=False):
    name = frappe.db.get_value("WAFD Stock Balance", {"warehouse": warehouse, "ingredient": ingredient}, "name")
    if name:
        doc = frappe.get_doc("WAFD Stock Balance", name)
        ingredient_uom = frappe.db.get_value("WAFD Ingredient", ingredient, "uom")
        if ingredient_uom and uom_matches(doc.uom, ingredient_uom):
            doc.uom = canonical_uom(ingredient_uom)
        if for_update:
            frappe.db.sql("select name from `tabWAFD Stock Balance` where name=%s for update", name)
            doc.reload()
        return doc
    ingredient_uom = frappe.db.get_value("WAFD Ingredient", ingredient, "uom")
    return frappe.get_doc({"doctype": "WAFD Stock Balance", "warehouse": warehouse, "ingredient": ingredient, "uom": canonical_uom(ingredient_uom or uom), "actual_quantity": 0, "reserved_quantity": 0, "average_cost": 0})


def _add_stock(warehouse, row, posting_date):
    balance = _get_balance(warehouse, row.ingredient, row.uom, for_update=True)
    old_qty = flt(balance.actual_quantity)
    incoming = flt(row.quantity)
    new_qty = old_qty + incoming
    if new_qty > 0:
        balance.average_cost = ((old_qty * flt(balance.average_cost)) + (incoming * flt(row.unit_cost))) / new_qty
    balance.actual_quantity = new_qty
    balance.last_movement_date = posting_date
    balance.save(ignore_permissions=True)


def _remove_stock(warehouse, row, posting_date):
    balance = _get_balance(warehouse, row.ingredient, row.uom, for_update=True)
    required = flt(row.quantity)
    available = flt(balance.available_quantity)
    if available < required:
        frappe.throw(f"المخزون غير كافٍ للصنف {row.ingredient}: المطلوب {required} والمتاح {available} / Insufficient stock")
    balance.actual_quantity = flt(balance.actual_quantity) - required
    balance.last_movement_date = posting_date
    balance.save(ignore_permissions=True)


def _remove_received_stock(warehouse, row, posting_date):
    """Reverse a receipt/addition without allowing negative or reserved stock.

    The weighted-average value is reversed algebraically so the balance returns
    to the value it had before this movement, provided later movements have not
    consumed the received quantity.
    """
    balance = _get_balance(warehouse, row.ingredient, row.uom, for_update=True)
    current_qty = flt(balance.actual_quantity)
    reverse_qty = flt(row.quantity)
    new_qty = current_qty - reverse_qty
    if new_qty < -0.000001:
        frappe.throw(
            f"لا يمكن عكس حركة المخزون {row.parent}: الكمية الحالية للصنف {row.ingredient} أقل من الكمية المستلمة "
            f"/ Cannot reverse stock movement: current quantity is below the received quantity"
        )
    if new_qty + 0.000001 < flt(balance.reserved_quantity):
        frappe.throw(
            f"لا يمكن عكس حركة المخزون للصنف {row.ingredient} لوجود كمية محجوزة "
            f"/ Cannot reverse movement while stock is reserved"
        )

    current_value = current_qty * flt(balance.average_cost)
    reversed_value = reverse_qty * flt(row.unit_cost)
    balance.actual_quantity = max(new_qty, 0)
    if new_qty > 0:
        remaining_value = current_value - reversed_value
        # Small negative values can be produced by decimal rounding only.
        if remaining_value < -0.01:
            frappe.throw(
                f"تعذر إعادة تكلفة المخزون بأمان للصنف {row.ingredient} "
                f"/ Unable to reverse stock valuation safely"
            )
        balance.average_cost = max(remaining_value, 0) / new_qty
    else:
        balance.average_cost = 0
    balance.last_movement_date = posting_date
    balance.save(ignore_permissions=True)



def analyze_reversal_safety(doc):
    """Return a non-mutating diagnostic for reversing one posted movement."""
    if isinstance(doc, str):
        doc = frappe.get_doc("WAFD Stock Movement", doc)
    result = {"name": doc.name, "safe": True, "blockers": [], "items": []}
    if doc.status != "مرحلة / Posted":
        return result
    if doc.movement_type == "تسوية / Adjustment":
        result["safe"] = False
        result["blockers"].append({
            "movement": doc.name,
            "reason": "adjustment",
            "message": "حركة تسوية لا تحتوي على رصيد ما قبل التسوية / Adjustment movement has no stored pre-adjustment balance",
        })
        return result

    checks = []
    for row in doc.items or []:
        if doc.movement_type == "استلام / Receipt":
            checks.append((doc.target_warehouse, row, "receipt"))
        elif doc.movement_type == "تحويل / Transfer":
            checks.append((doc.target_warehouse, row, "transfer_target"))

    for warehouse, row, role in checks:
        balance = _get_balance(warehouse, row.ingredient, row.uom)
        current_qty = flt(balance.actual_quantity)
        reserved_qty = flt(balance.reserved_quantity)
        required_qty = flt(row.quantity)
        item = {
            "movement": doc.name, "ingredient": row.ingredient, "warehouse": warehouse,
            "required_quantity": required_qty, "current_quantity": current_qty,
            "reserved_quantity": reserved_qty, "role": role, "dependencies": [],
        }
        shortage = max(required_qty - current_qty, 0)
        reserved_block = max((reserved_qty + required_qty) - current_qty, 0)
        if shortage > 0.000001 or reserved_block > 0.000001:
            result["safe"] = False
            later = frappe.db.sql(
                """select distinct sm.name, sm.movement_type, sm.posting_date
                   from `tabWAFD Stock Movement` sm
                   join `tabWAFD Stock Movement Item` i on i.parent=sm.name
                  where sm.status='مرحلة / Posted' and coalesce(sm.is_pre_go_live_test,0)=0 and sm.name!=%s and i.ingredient=%s
                    and sm.posting_date >= %s
                    and ((sm.source_warehouse=%s and sm.movement_type in ('صرف / Issue','هالك / Waste','تحويل / Transfer'))
                         or (sm.target_warehouse=%s and sm.movement_type='تسوية / Adjustment'))
                  order by sm.posting_date desc, sm.creation desc limit 20""",
                (doc.name, row.ingredient, doc.posting_date, warehouse, warehouse), as_dict=True
            )
            item["dependencies"] = later
            item["shortage"] = shortage
            item["reserved_block"] = reserved_block
            result["blockers"].append(item)
        result["items"].append(item)
    return result

def reverse_posted_movement(doc, reason=None):
    """Reverse one posted WAFD stock movement exactly once.

    This is used by the contract reset/purge workflow.  It deliberately blocks
    Adjustment movements because the pre-adjustment quantity is not stored in
    legacy documents and guessing it could corrupt stock.
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("WAFD Stock Movement", doc)
    if doc.get("is_pre_go_live_test"):
        return {"name": doc.name, "reversed": False, "items": 0, "archived_pre_go_live": True}
    if doc.status != "مرحلة / Posted":
        return {"name": doc.name, "reversed": False, "items": 0}
    if doc.movement_type == "تسوية / Adjustment":
        frappe.throw(
            f"لا يمكن حذف العقد لأن حركة التسوية {doc.name} لا تحتوي على رصيد ما قبل التسوية. "
            f"ألغِ التسوية يدويًا أولًا / Contract purge blocked: adjustment movement must be reversed manually first"
        )

    frappe.db.sql("select name from `tabWAFD Stock Movement` where name=%s for update", doc.name)
    doc.reload()
    if doc.status != "مرحلة / Posted":
        return {"name": doc.name, "reversed": False, "items": 0}

    for row in doc.items or []:
        if doc.movement_type == "استلام / Receipt":
            _remove_received_stock(doc.target_warehouse, row, now_datetime())
        elif doc.movement_type in ("صرف / Issue", "هالك / Waste"):
            _add_stock(doc.source_warehouse, row, now_datetime())
        elif doc.movement_type == "تحويل / Transfer":
            # Reverse in the opposite order: remove from target, restore source.
            _remove_received_stock(doc.target_warehouse, row, now_datetime())
            _add_stock(doc.source_warehouse, row, now_datetime())
        else:
            frappe.throw(f"نوع حركة غير مدعوم للعكس: {doc.movement_type} / Unsupported reversal type")

    doc.db_set(
        {
            "status": "ملغاة / Cancelled",
            "posted_by": None,
            "posted_on": None,
        },
        update_modified=True,
    )
    if doc.reference_type == "WAFD Purchase Order" and doc.reference_name:
        from wafd_one.wafd_one.doctype.wafd_purchase_order.wafd_purchase_order import sync_purchase_order_receipts
        sync_purchase_order_receipts(doc.reference_name)
    if doc.production_batch and frappe.db.exists("WAFD Production Batch", doc.production_batch):
        frappe.db.set_value(
            "WAFD Production Batch",
            doc.production_batch,
            {"material_issue": None, "materials_status": "غير مصروفة / Not Issued"},
            update_modified=False,
        )
    frappe.logger("wafd_one").warning(
        "Stock movement reversed by %s: %s (%s)",
        frappe.session.user,
        doc.name,
        reason or "manual",
    )
    return {"name": doc.name, "reversed": True, "items": len(doc.items or [])}


@frappe.whitelist()
def post_movement(movement_name):
    doc = frappe.get_doc("WAFD Stock Movement", movement_name)
    doc.check_permission("write")
    if doc.get("is_pre_go_live_test"):
        frappe.throw("هذه حركة اختبار مؤرشفة قبل التشغيل الفعلي ولا يمكن ترحيلها / Archived pre-Go-Live test movements cannot be posted")
    frappe.db.sql("select name from `tabWAFD Stock Movement` where name=%s for update", movement_name)
    doc.reload()
    if doc.status == "مرحلة / Posted":
        return {"name": doc.name, "posted": False}
    if doc.status == "ملغاة / Cancelled":
        frappe.throw("لا يمكن ترحيل حركة ملغاة / A cancelled movement cannot be posted")
    doc.validate()
    if not doc.items:
        frappe.throw("أضف صنفًا واحدًا على الأقل / Add at least one item")
    for row in doc.items:
        if doc.movement_type == "استلام / Receipt":
            _add_stock(doc.target_warehouse, row, doc.posting_date)
        elif doc.movement_type in ("صرف / Issue", "هالك / Waste"):
            _remove_stock(doc.source_warehouse, row, doc.posting_date)
        elif doc.movement_type == "تحويل / Transfer":
            _remove_stock(doc.source_warehouse, row, doc.posting_date)
            _add_stock(doc.target_warehouse, row, doc.posting_date)
        elif doc.movement_type == "تسوية / Adjustment":
            warehouse = doc.target_warehouse or doc.source_warehouse
            if not warehouse:
                frappe.throw("حدد مستودع التسوية / Select adjustment warehouse")
            balance = _get_balance(warehouse, row.ingredient, row.uom, for_update=True)
            balance.actual_quantity = flt(row.quantity)
            balance.average_cost = flt(row.unit_cost) or flt(balance.average_cost)
            balance.last_movement_date = doc.posting_date
            balance.save(ignore_permissions=True)
    doc.db_set({"status": "مرحلة / Posted", "posted_by": frappe.session.user, "posted_on": now_datetime()}, update_modified=True)
    if doc.reference_type == "WAFD Purchase Order" and doc.reference_name:
        from wafd_one.wafd_one.doctype.wafd_purchase_order.wafd_purchase_order import sync_purchase_order_receipts
        sync_purchase_order_receipts(doc.reference_name)
    from wafd_one.costing import refresh_costs_after_stock_movement
    refresh_costs_after_stock_movement(doc)
    if doc.production_batch and frappe.db.exists("WAFD Production Batch", doc.production_batch):
        frappe.db.set_value(
            "WAFD Production Batch", doc.production_batch,
            {"material_issue": doc.name, "materials_status": "مصروفة / Issued"},
            update_modified=False,
        )
    return {"name": doc.name, "posted": True}
