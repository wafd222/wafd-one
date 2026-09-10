import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class WAFDCleaningMaterialUsage(Document):
    def validate(self):
        self.supervisor = self.supervisor or frappe.session.user
        self.usage_date = self.usage_date or now_datetime()
        self.recorded_by = self.recorded_by or frappe.session.user
        self.recorded_on = self.recorded_on or now_datetime()
        self.status = "مسجل / Recorded"

        roles = set(frappe.get_roles())
        restricted = "WAFD Cleaning Supervisor" in roles and not roles.intersection(
            {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}
        )
        if restricted and self.supervisor != frappe.session.user:
            frappe.throw("لا يمكنك التسجيل لمشرف آخر / You cannot record usage for another supervisor")

        movement = frappe.get_doc("WAFD Stock Movement", self.source_handover)
        if movement.issued_to_user != self.supervisor:
            frappe.throw("سند التسليم لا يخص هذا المشرف / The handover is not assigned to this supervisor")
        if movement.handover_status != "تم الاستلام / Received":
            frappe.throw("يجب تأكيد الاستلام قبل تسجيل الصرف / Accept the handover before recording usage")

        allowed = {row.ingredient: row for row in movement.items or []}
        seen = set()
        for row in self.items or []:
            if row.ingredient in seen:
                frappe.throw("لا تكرر المادة في السجل / Do not repeat an item")
            seen.add(row.ingredient)
            if row.ingredient not in allowed:
                frappe.throw(f"المادة {row.ingredient} غير موجودة في سند التسليم / Item is not in the handover")
            if flt(row.quantity) <= 0:
                frappe.throw("الكمية المصروفة يجب أن تكون أكبر من صفر / Used quantity must be greater than zero")
            row.uom = allowed[row.ingredient].uom
            prior = frappe.db.sql(
                """select coalesce(sum(i.quantity), 0)
                     from `tabWAFD Cleaning Material Usage Item` i
                     join `tabWAFD Cleaning Material Usage` u on u.name=i.parent
                    where u.source_handover=%s and i.ingredient=%s and u.name!=%s""",
                (self.source_handover, row.ingredient, self.name or ""),
            )[0][0]
            if flt(prior) + flt(row.quantity) > flt(allowed[row.ingredient].quantity) + 0.000001:
                frappe.throw("الكمية تتجاوز الرصيد الموجود لدى المشرف / Quantity exceeds the supervisor custody balance")

    def before_delete(self):
        frappe.throw("لا يمكن حذف سجل صرف النظافة / Cleaning usage records cannot be deleted")
