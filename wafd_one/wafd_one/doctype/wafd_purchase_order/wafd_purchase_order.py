import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime


CANCELLED = "ملغي / Cancelled"
RECEIVED = "مستلم / Received"
PARTIALLY_RECEIVED = "مستلم جزئياً / Partially Received"


class WAFDPurchaseOrder(Document):
    def validate(self):
        from wafd_one.governance import ensure_approved
        if self.status not in ("مسودة / Draft", "ملغي / Cancelled") and not self.is_new():
            previous = self.get_doc_before_save()
            if previous and previous.status != self.status:
                ensure_approved(self, "اعتماد أمر الشراء / purchase order approval")
        self._validate_header()
        self._validate_items()
        self._calculate_totals()
        self._derive_receipt_status()

    def _validate_header(self):
        if self.expected_date and getdate(self.expected_date) < getdate(self.order_date):
            frappe.throw("تاريخ التوريد المتوقع لا يمكن أن يسبق تاريخ الطلب / Expected date cannot be before order date")
        if not self.items:
            frappe.throw("أضف صنفاً واحداً على الأقل / Add at least one item")
        if self.status == CANCELLED and self.name and _has_posted_receipts(self.name):
            frappe.throw("لا يمكن إلغاء أمر شراء لديه استلامات مرحلة / A purchase order with posted receipts cannot be cancelled")

    def _validate_items(self):
        seen = set()
        for row in self.items or []:
            if row.ingredient in seen:
                frappe.throw(f"المكون مكرر في أمر الشراء: {row.ingredient} / Duplicate ingredient")
            seen.add(row.ingredient)
            if flt(row.quantity) <= 0:
                frappe.throw("كمية الشراء يجب أن تكون أكبر من صفر / Purchase quantity must be greater than zero")
            if flt(row.rate) < 0:
                frappe.throw("سعر الشراء لا يمكن أن يكون سالباً / Purchase rate cannot be negative")
            if flt(row.received_quantity) < 0:
                frappe.throw("الكمية المستلمة لا يمكن أن تكون سالبة / Received quantity cannot be negative")
            if flt(row.received_quantity) > flt(row.quantity):
                frappe.throw(f"الكمية المستلمة تتجاوز المطلوبة للصنف {row.ingredient} / Received quantity exceeds ordered quantity")
            ingredient = frappe.db.get_value(
                "WAFD Ingredient", row.ingredient, ["is_active", "uom"], as_dict=True
            )
            if not ingredient or not ingredient.is_active:
                frappe.throw(f"المكون غير نشط: {row.ingredient} / Ingredient is inactive")
            if not row.uom:
                row.uom = ingredient.uom
            elif ingredient.uom and row.uom != ingredient.uom:
                frappe.throw(
                    f"وحدة الصنف {row.ingredient} يجب أن تكون {ingredient.uom} / Ingredient UOM mismatch"
                )

    def _calculate_totals(self):
        subtotal = 0
        for row in self.items or []:
            row.amount = flt(row.quantity) * flt(row.rate)
            subtotal += row.amount
        tax_rate = flt(self.tax_rate)
        if tax_rate < 0 or tax_rate > 100:
            frappe.throw("نسبة الضريبة يجب أن تكون بين صفر و100 / Tax rate must be between 0 and 100")
        self.subtotal = subtotal
        self.tax_amount = subtotal * tax_rate / 100
        self.grand_total = subtotal + self.tax_amount

    def _derive_receipt_status(self):
        if self.status == CANCELLED:
            return
        total_ordered = sum(flt(row.quantity) for row in self.items or [])
        total_received = sum(flt(row.received_quantity) for row in self.items or [])
        if total_ordered and total_received >= total_ordered:
            self.status = RECEIVED
        elif total_received > 0:
            self.status = PARTIALLY_RECEIVED
        elif self.status in (RECEIVED, PARTIALLY_RECEIVED):
            self.status = "معتمد / Approved"

    def before_delete(self):
        if _has_posted_receipts(self.name):
            frappe.throw("لا يمكن حذف أمر شراء لديه استلامات مرحلة / A purchase order with posted receipts cannot be deleted")


def _has_posted_receipts(purchase_order_name):
    return bool(frappe.db.exists("WAFD Stock Movement", {
        "movement_type": "استلام / Receipt",
        "reference_type": "WAFD Purchase Order",
        "reference_name": purchase_order_name,
        "status": "مرحلة / Posted",
    }))


def _receipt_totals(purchase_order_name):
    totals = {}
    movement_names = frappe.get_all(
        "WAFD Stock Movement",
        filters={
            "movement_type": "استلام / Receipt",
            "reference_type": "WAFD Purchase Order",
            "reference_name": purchase_order_name,
            "status": "مرحلة / Posted",
        },
        pluck="name",
    )
    for movement_name in movement_names:
        movement = frappe.get_doc("WAFD Stock Movement", movement_name)
        for row in movement.items or []:
            totals[row.ingredient] = totals.get(row.ingredient, 0) + flt(row.quantity)
    return totals


def sync_purchase_order_receipts(purchase_order_name):
    if not purchase_order_name or not frappe.db.exists("WAFD Purchase Order", purchase_order_name):
        return
    po = frappe.get_doc("WAFD Purchase Order", purchase_order_name)
    totals = _receipt_totals(purchase_order_name)
    total_ordered = 0
    total_received = 0
    for row in po.items or []:
        received = totals.get(row.ingredient, 0)
        if flt(received) > flt(row.quantity) + 0.000001:
            frappe.throw(
                f"إجمالي الاستلام يتجاوز أمر الشراء للصنف {row.ingredient} / Total receipts exceed ordered quantity"
            )
        frappe.db.set_value("WAFD Purchase Order Item", row.name, "received_quantity", received, update_modified=False)
        total_ordered += flt(row.quantity)
        total_received += flt(received)
    if po.status != CANCELLED:
        if total_ordered and total_received >= total_ordered:
            status = RECEIVED
        elif total_received > 0:
            status = PARTIALLY_RECEIVED
        elif po.status in (RECEIVED, PARTIALLY_RECEIVED):
            status = "معتمد / Approved"
        else:
            status = po.status
        frappe.db.set_value("WAFD Purchase Order", po.name, "status", status, update_modified=True)


@frappe.whitelist()
def create_goods_receipt(purchase_order_name):
    po = frappe.get_doc("WAFD Purchase Order", purchase_order_name)
    po.check_permission("write")
    if po.status == CANCELLED:
        frappe.throw("لا يمكن الاستلام على أمر شراء ملغي / Cannot receive a cancelled purchase order")
    if po.status == "مسودة / Draft":
        frappe.throw("اعتمد أمر الشراء قبل إنشاء الاستلام / Approve the purchase order before receiving")

    existing_draft = frappe.db.get_value(
        "WAFD Stock Movement",
        {
            "movement_type": "استلام / Receipt",
            "reference_type": "WAFD Purchase Order",
            "reference_name": po.name,
            "status": "مسودة / Draft",
        },
        "name",
    )
    if existing_draft:
        return {"name": existing_draft, "created": False}

    receipt = frappe.get_doc({
        "doctype": "WAFD Stock Movement",
        "movement_type": "استلام / Receipt",
        "posting_date": now_datetime(),
        "project": po.project,
        "target_warehouse": po.warehouse,
        "reference_type": "WAFD Purchase Order",
        "reference_name": po.name,
        "status": "مسودة / Draft",
        "notes": f"استلام مشتريات لأمر الشراء {po.name}",
    })
    for row in po.items or []:
        outstanding = flt(row.quantity) - flt(row.received_quantity)
        if outstanding > 0:
            receipt.append("items", {
                "ingredient": row.ingredient,
                "quantity": outstanding,
                "uom": row.uom,
                "unit_cost": row.rate,
            })
    if not receipt.items:
        frappe.throw("تم استلام جميع أصناف أمر الشراء / All purchase order items are fully received")
    receipt.insert()
    return {"name": receipt.name, "created": True}
