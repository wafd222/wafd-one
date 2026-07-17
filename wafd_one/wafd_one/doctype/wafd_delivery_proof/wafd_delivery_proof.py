import frappe
from frappe.model.document import Document
from frappe.utils import cint


class WafdDeliveryProof(Document):
    def validate(self):
        trip = frappe.db.get_value("WAFD Delivery Trip", self.delivery_trip, ["project","meal_plan","hotel","quantity","status"], as_dict=True)
        if not trip: frappe.throw("رحلة التوصيل غير موجودة / Delivery trip not found")
        if trip.status == "ملغية / Cancelled": frappe.throw("لا يمكن إثبات تسليم رحلة ملغية / Cannot confirm a cancelled trip")
        self.project, self.meal_plan, self.hotel, self.delivered_quantity = trip.project, trip.meal_plan, trip.hotel, cint(trip.quantity)
        received, rejected = cint(self.received_quantity), cint(self.rejected_quantity)
        if min(received, rejected) < 0: frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
        if received + rejected != cint(trip.quantity): frappe.throw("المستلم والمرفوض يجب أن يساويا كمية الرحلة / Received plus rejected must equal trip quantity")
        if self.status == "مقبول بالكامل / Fully Accepted" and rejected: frappe.throw("لا يمكن وجود كمية مرفوضة مع قبول كامل / Fully accepted delivery cannot include rejected quantity")
        if self.status == "مرفوض / Rejected" and received: frappe.throw("الاستلام يجب أن يكون صفراً عند الرفض / Received quantity must be zero when rejected")
        if self.status != "مرفوض / Rejected" and not self.receiver_signature: frappe.throw("توقيع المستلم مطلوب / Receiver signature is required")
        if not self.delivery_photo: frappe.throw("صورة التسليم مطلوبة / Delivery photo is required")

    def on_update(self):
        frappe.db.set_value("WAFD Delivery Trip", self.delivery_trip, "status", "تم التسليم / Delivered", update_modified=False)
        if self.meal_plan:
            total = frappe.db.sql("select coalesce(sum(dp.received_quantity),0) from `tabWAFD Delivery Proof` dp inner join `tabWAFD Delivery Trip` dt on dt.name=dp.delivery_trip where dt.meal_plan=%s", self.meal_plan)[0][0]
            planned = cint(frappe.db.get_value("WAFD Meal Plan", self.meal_plan, "quantity") or 0)
            if cint(total) >= planned: frappe.db.set_value("WAFD Meal Plan", self.meal_plan, "status", "تم التسليم / Delivered", update_modified=False)
