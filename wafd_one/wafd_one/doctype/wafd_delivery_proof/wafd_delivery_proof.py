import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now_datetime


class WAFDDeliveryProof(Document):
    def validate(self):
        trip = frappe.db.get_value("WAFD Delivery Trip", self.delivery_trip,
            ["project", "meal_plan", "hotel", "quantity", "status", "actual_departure"], as_dict=True)
        if not trip:
            frappe.throw("رحلة التوصيل غير موجودة / Delivery trip not found")
        if trip.status == "ملغية / Cancelled":
            frappe.throw("لا يمكن إثبات تسليم رحلة ملغاة / Cannot confirm a cancelled trip")
        duplicate = frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": self.delivery_trip, "name": ["!=", self.name or ""]})
        if duplicate:
            frappe.throw("يوجد إثبات تسليم لهذه الرحلة بالفعل / Delivery proof already exists for this trip")
        self.project, self.meal_plan, self.hotel = trip.project, trip.meal_plan, trip.hotel
        received, rejected = cint(self.received_quantity), cint(self.rejected_quantity)
        self.delivered_quantity = received
        if min(received, rejected) < 0:
            frappe.throw("الكميات لا يمكن أن تكون سالبة / Quantities cannot be negative")
        if received + rejected != cint(trip.quantity):
            frappe.throw("المستلم والمرفوض يجب أن يساويا كمية الرحلة / Received plus rejected must equal trip quantity")
        if self.status == "مقبول بالكامل / Fully Accepted" and rejected:
            frappe.throw("لا يمكن وجود كمية مرفوضة مع قبول كامل / Fully accepted delivery cannot include rejected quantity")
        if self.status == "مقبول جزئياً / Partially Accepted" and (received <= 0 or rejected <= 0):
            frappe.throw("القبول الجزئي يتطلب كمية مستلمة ومرفوضة / Partial acceptance requires received and rejected quantities")
        if self.status == "مرفوض / Rejected" and (received or rejected != cint(trip.quantity)):
            frappe.throw("عند الرفض يجب أن تكون كامل كمية الرحلة مرفوضة / Rejected delivery must reject the full trip quantity")
        if not (self.receiver_name or "").strip():
            frappe.throw("اسم المستلم مطلوب / Receiver name is required")
        if self.status != "مرفوض / Rejected" and not self.receiver_signature:
            frappe.throw("توقيع المستلم مطلوب / Receiver signature is required")
        if not self.delivery_photo:
            frappe.throw("صورة التسليم مطلوبة / Delivery photo is required")
        if self.delivery_time and get_datetime(self.delivery_time) > now_datetime():
            frappe.throw("وقت التسليم لا يمكن أن يكون في المستقبل / Delivery time cannot be in the future")
        if trip.actual_departure and self.delivery_time and get_datetime(self.delivery_time) < get_datetime(trip.actual_departure):
            frappe.throw("وقت التسليم لا يمكن أن يسبق المغادرة / Delivery time cannot be before departure")
        if self.latitude is not None and self.latitude != "" and not (-90 <= flt(self.latitude) <= 90):
            frappe.throw("خط العرض غير صحيح / Invalid latitude")
        if self.longitude is not None and self.longitude != "" and not (-180 <= flt(self.longitude) <= 180):
            frappe.throw("خط الطول غير صحيح / Invalid longitude")

    def on_update(self):
        frappe.db.set_value("WAFD Delivery Trip", self.delivery_trip, {"status": "تم التسليم / Delivered", "actual_arrival": self.delivery_time}, update_modified=False)
        trip = frappe.db.get_value("WAFD Delivery Trip", self.delivery_trip, ["vehicle", "driver"], as_dict=True)
        if trip:
            from wafd_one.wafd_one.doctype.wafd_delivery_trip.wafd_delivery_trip import _sync_resource_statuses
            _sync_resource_statuses(trip.vehicle, trip.driver)
        self._sync_meal_plan()

    def on_trash(self):
        trip = frappe.db.get_value("WAFD Delivery Trip", self.delivery_trip, ["vehicle", "driver"], as_dict=True)
        frappe.db.set_value("WAFD Delivery Trip", self.delivery_trip, "status", "وصلت / Arrived", update_modified=False)
        self._sync_meal_plan(exclude_name=self.name)
        if trip:
            from wafd_one.wafd_one.doctype.wafd_delivery_trip.wafd_delivery_trip import _sync_resource_statuses
            _sync_resource_statuses(trip.vehicle, trip.driver)

    def _sync_meal_plan(self, exclude_name=None):
        if not self.meal_plan:
            return
        condition, params = "", [self.meal_plan]
        if exclude_name:
            condition, params = " and dp.name!=%s", [self.meal_plan, exclude_name]
        total = frappe.db.sql("""select coalesce(sum(dp.received_quantity),0)
            from `tabWAFD Delivery Proof` dp inner join `tabWAFD Delivery Trip` dt on dt.name=dp.delivery_trip
            where dt.meal_plan=%s""" + condition, params)[0][0]
        planned = cint(frappe.db.get_value("WAFD Meal Plan", self.meal_plan, "quantity") or 0)
        status = "تم التسليم / Delivered" if planned and cint(total) >= planned else "جاهز / Ready"
        frappe.db.set_value("WAFD Meal Plan", self.meal_plan, "status", status, update_modified=False)
