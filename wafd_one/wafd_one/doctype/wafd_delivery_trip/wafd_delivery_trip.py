import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, get_datetime, getdate, now_datetime, nowdate

from wafd_one.driver_security import resolve_linked_driver

ACTIVE = ("مخططة / Planned", "تم التحميل / Loaded", "في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed")


class WAFDDeliveryTrip(Document):
    def validate(self):
        self.trip_source = self.trip_source or (
            "سجل تحميل / Loading Record" if self.loading_record
            else "خطة مشرف التوصيل / Delivery Supervisor Plan"
        )
        supervisor_plan = self.trip_source == "خطة مشرف التوصيل / Delivery Supervisor Plan"
        if supervisor_plan:
            loading = None
            self._validate_supervisor_plan()
        else:
            self._validate_loading_trip()
            loading = frappe.db.get_value(
                "WAFD Loading Record", self.loading_record,
                ["name", "project", "meal_plan", "vehicle", "driver", "hotel", "quantity", "status", "dispatch_time", "loading_date"],
                as_dict=True,
            )

        if loading:
            duplicate = frappe.db.exists("WAFD Delivery Trip", {"loading_record": self.loading_record, "name": ["!=", self.name or ""], "status": ["!=", "ملغية / Cancelled"]})
            if duplicate:
                frappe.throw("يوجد بالفعل رحلة غير ملغاة لسجل التحميل / A non-cancelled trip already exists for this loading record")
            if self.quantity <= 0:
                frappe.throw("كمية الرحلة يجب أن تكون أكبر من صفر / Trip quantity must be greater than zero")
            self._validate_resource(self.vehicle, self.driver)
            self._validate_food_safety_release()
            self._fill_planned_times(loading)
        elif cint(self.quantity) < 0:
            frappe.throw("عدد الوجبات لا يمكن أن يكون سالباً / Meal quantity cannot be negative")

        # Loaded/planned trips have not departed yet. This also repairs any
        # premature or future actual departure saved by older release retries.
        if self.status in ("مخططة / Planned", "تم التحميل / Loaded"):
            self.actual_departure = None
            self.actual_arrival = None

        # Populate actual timestamps before validating and calculating metrics.
        if self.status == "في الطريق / In Transit":
            self.actual_departure = self.actual_departure or (loading.dispatch_time if loading else None) or now_datetime()
        if self.status in ("وصلت / Arrived", "تم التسليم / Delivered"):
            self.actual_arrival = self.actual_arrival or now_datetime()
            if not self.actual_departure:
                self.actual_departure = (loading.dispatch_time or loading.loading_date) if loading else now_datetime()

        self._validate_times()
        self._calculate_trip_metrics()

        if self.status == "متأخرة / Delayed" and not (self.delay_reason or "").strip():
            frappe.throw("سبب التأخير مطلوب / Delay reason is required")
        if self.status == "تم التسليم / Delivered" and not frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": self.name}):
            frappe.throw("لا يمكن اعتماد الرحلة مسلمة دون إثبات تسليم / Delivery proof is required")

    def _validate_loading_trip(self):
        loading = frappe.db.get_value("WAFD Loading Record", self.loading_record,
            ["project", "meal_plan", "vehicle", "driver", "hotel", "quantity", "status", "dispatch_time", "loading_date"], as_dict=True)
        if not loading:
            frappe.throw("سجل التحميل غير موجود / Loading record not found")
        if loading.status not in ("تم التحميل / Loaded", "خرجت / Dispatched"):
            frappe.throw("يجب إكمال التحميل أولاً / Loading must be completed first")
        self.project, self.meal_plan, self.vehicle, self.driver, self.hotel = loading.project, loading.meal_plan, loading.vehicle, loading.driver, loading.hotel
        self.quantity = cint(loading.quantity)
        self.trip_date = self.trip_date or nowdate()

        canonical_driver, driver_user = resolve_linked_driver(self.driver)
        if not canonical_driver or not driver_user:
            frappe.throw(
                "السائق المختار غير مرتبط بشكل فريد بحساب سائق مفعل. راجع إدارة الموظفين / "
                "The selected driver is not uniquely linked to an enabled Driver user"
            )
        if canonical_driver != self.driver:
            frappe.db.set_value(
                "WAFD Loading Record", loading.name, "driver", canonical_driver, update_modified=False
            )
            self.driver = canonical_driver
        self.assigned_driver_user = driver_user

    def _validate_supervisor_plan(self):
        self.loading_record = None
        self.project = self.project or None
        self.meal_plan = self.meal_plan or None
        self.trip_date = self.trip_date or nowdate()
        self.quantity = max(cint(self.quantity), 0)
        self.meal_type = self.meal_type or "غداء / Lunch"

        if self.hotel:
            hotel = frappe.db.get_value(
                "WAFD Hotel", self.hotel,
                ["hotel_name_ar", "hotel_name_en", "map_url", "latitude", "longitude", "status"],
                as_dict=True,
            )
            if not hotel or hotel.status == "غير نشط / Inactive":
                frappe.throw("اختر فندقاً نشطاً / Select an active hotel")
            self.delivery_kind = "فندق / Hotel"
            self.destination_name = hotel.hotel_name_ar or self.hotel
            self.destination_name_en = hotel.hotel_name_en or self.destination_name
            self.destination_map_url = self.destination_map_url or hotel.map_url
            self.destination_latitude = self.destination_latitude or hotel.latitude
            self.destination_longitude = self.destination_longitude or hotel.longitude
        elif self.delivery_location:
            location = frappe.db.get_value(
                "WAFD Delivery Location", self.delivery_location,
                ["location_name_ar", "location_name_en", "location_type", "map_url", "latitude", "longitude", "status"],
                as_dict=True,
            )
            if not location or location.status == "غير نشط / Inactive":
                frappe.throw("اختر موقع توصيل نشطاً / Select an active delivery location")
            self.delivery_kind = self.delivery_kind or location.location_type
            self.destination_name = location.location_name_ar or self.delivery_location
            self.destination_name_en = location.location_name_en or self.destination_name
            self.destination_map_url = self.destination_map_url or location.map_url
            self.destination_latitude = self.destination_latitude or location.latitude
            self.destination_longitude = self.destination_longitude or location.longitude
        if not (self.destination_name or "").strip():
            frappe.throw("اختر الفندق أو موقع التوصيل / Choose a hotel or delivery location")
        if not self.planned_arrival:
            frappe.throw("وقت التوصيل مطلوب / Delivery time is required")
        if not self.driver:
            frappe.throw("اختر السائق / Select a driver")

        canonical_driver, driver_user = resolve_linked_driver(self.driver)
        if not canonical_driver or not driver_user:
            frappe.throw("السائق غير مرتبط بحساب سائق مفعل / Driver is not linked to an enabled account")
        self.driver = canonical_driver
        self.assigned_driver_user = driver_user
        driver = frappe.db.get_value("WAFD Driver", self.driver, ["status", "license_expiry"], as_dict=True)
        if not driver or driver.status in ("إجازة / Leave", "غير نشط / Inactive"):
            frappe.throw("السائق غير متاح / Driver is unavailable")
        if driver.license_expiry and getdate(driver.license_expiry) < getdate(nowdate()):
            frappe.throw("رخصة السائق منتهية / Driver license has expired")
        if self.vehicle:
            vehicle = frappe.db.get_value("WAFD Vehicle", self.vehicle, ["status", "registration_expiry", "insurance_expiry"], as_dict=True)
            if not vehicle or vehicle.status in ("صيانة / Maintenance", "غير نشطة / Inactive"):
                frappe.throw("المركبة غير متاحة / Vehicle is unavailable")


    def _fill_planned_times(self, loading):
        """Derive auditable trip targets from the meal service schedule.

        Planned arrival is the service time minus the configured delivery lead
        minutes. Planned departure uses the loading schedule timestamp because
        the current data model has no route-duration master; we do not invent a
        travel duration.
        """
        loading_time = loading.loading_date or loading.dispatch_time
        if self.planned_arrival:
            if not self.planned_departure:
                # A late loading record must not make the planned pair invalid.
                # Preserve the original arrival target for delay measurement.
                self.planned_departure = min(get_datetime(loading_time), get_datetime(self.planned_arrival)) if loading_time else self.planned_arrival
            return
        plan = frappe.db.get_value(
            "WAFD Meal Plan", self.meal_plan,
            ["service_date", "service_time", "meal_type", "project"], as_dict=True,
        )
        if not plan or not plan.service_date or not plan.service_time:
            return
        lead_minutes = frappe.db.get_value(
            "WAFD Project Service",
            {
                "parent": plan.project or self.project,
                "parenttype": "WAFD Catering Project",
                "service_type": plan.meal_type,
            },
            "delivery_lead_minutes",
        )
        lead_minutes = cint(lead_minutes) if lead_minutes not in (None, "") else 45
        service_dt = get_datetime(f"{plan.service_date} {plan.service_time}")
        target_arrival = add_to_date(service_dt, minutes=-lead_minutes, as_datetime=True)
        self.planned_arrival = target_arrival
        if not self.planned_departure:
            # Loading can happen after the scheduled arrival during delayed or
            # test operations. Keep the target arrival so delay remains
            # auditable, while preventing an impossible planned time pair.
            self.planned_departure = min(get_datetime(loading_time), get_datetime(target_arrival)) if loading_time else target_arrival

    def _calculate_trip_metrics(self):
        self.delay_minutes = 0
        self.transit_duration_minutes = 0
        self.on_time_status = "غير محدد / Not Set"
        if self.actual_departure and self.actual_arrival:
            seconds = (get_datetime(self.actual_arrival) - get_datetime(self.actual_departure)).total_seconds()
            self.transit_duration_minutes = max(int(seconds // 60), 0)
        comparison_time = self.actual_arrival
        if not comparison_time and self.status in ("في الطريق / In Transit", "متأخرة / Delayed"):
            comparison_time = now_datetime()
        if self.planned_arrival and comparison_time:
            minutes = int((get_datetime(comparison_time) - get_datetime(self.planned_arrival)).total_seconds() // 60)
            self.delay_minutes = max(minutes, 0)
            self.on_time_status = "متأخر / Delayed" if minutes > 0 else "في الوقت / On Time"

    def _validate_resource(self, vehicle_name, driver_name):
        vehicle = frappe.db.get_value("WAFD Vehicle", vehicle_name, ["status", "capacity_meals", "registration_expiry", "insurance_expiry"], as_dict=True)
        driver = frappe.db.get_value("WAFD Driver", driver_name, ["status", "license_expiry"], as_dict=True)
        if not vehicle or not driver:
            frappe.throw("المركبة أو السائق غير موجود / Vehicle or driver was not found")
        if vehicle.status in ("صيانة / Maintenance", "غير نشطة / Inactive"):
            frappe.throw("المركبة غير صالحة للرحلة / Vehicle is unavailable")
        if driver.status in ("إجازة / Leave", "غير نشط / Inactive"):
            frappe.throw("السائق غير صالح للرحلة / Driver is unavailable")
        if cint(vehicle.capacity_meals) and self.quantity > cint(vehicle.capacity_meals):
            frappe.throw("كمية الرحلة تتجاوز سعة المركبة / Trip quantity exceeds vehicle capacity")
        today = getdate(nowdate())
        if vehicle.registration_expiry and getdate(vehicle.registration_expiry) < today:
            frappe.throw("استمارة المركبة منتهية / Vehicle registration has expired")
        if vehicle.insurance_expiry and getdate(vehicle.insurance_expiry) < today:
            frappe.throw("تأمين المركبة منتهٍ / Vehicle insurance has expired")
        if driver.license_expiry and getdate(driver.license_expiry) < today:
            frappe.throw("رخصة السائق منتهية / Driver license has expired")
        if self.status in ACTIVE:
            for dt, resource in (("vehicle", vehicle_name), ("driver", driver_name)):
                conflict = frappe.db.exists("WAFD Delivery Trip", {dt: resource, "name": ["!=", self.name or ""], "status": ["in", ACTIVE]})
                if conflict:
                    frappe.throw("المركبة أو السائق مرتبط برحلة نشطة أخرى / Vehicle or driver is assigned to another active trip")


    def _validate_food_safety_release(self):
        if self.status not in ("تم التحميل / Loaded", "في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed", "تم التسليم / Delivered"):
            return
        batches = frappe.get_all(
            "WAFD Production Batch",
            filters={"meal_plan": self.meal_plan},
            fields=["name", "food_safety_release_status"],
        )
        if not batches:
            frappe.throw("لا توجد دفعة إنتاج مرتبطة بخطة الوجبة / No production batch is linked to the meal plan")
        blocked = [row.name for row in batches if row.food_safety_release_status != "مفرج / Released"]
        if blocked:
            frappe.throw("لا يمكن تحريك الرحلة قبل الإفراج الغذائي عن الدفعات: " + ", ".join(blocked) + " / Food safety release is required")

    def _validate_times(self):
        pairs = (("planned_departure", "planned_arrival"), ("actual_departure", "actual_arrival"))
        for start, end in pairs:
            if self.get(start) and self.get(end) and get_datetime(self.get(end)) < get_datetime(self.get(start)):
                frappe.throw("وقت الوصول لا يمكن أن يسبق وقت المغادرة / Arrival cannot be before departure")
        if self.actual_departure and get_datetime(self.actual_departure) > now_datetime():
            frappe.throw("وقت المغادرة الفعلي لا يمكن أن يكون مستقبلياً / Actual departure cannot be in the future")
        if self.actual_arrival and get_datetime(self.actual_arrival) > now_datetime():
            frappe.throw("وقت الوصول الفعلي لا يمكن أن يكون مستقبلياً / Actual arrival cannot be in the future")

    def on_update(self):
        if self.loading_record and self.status in ("في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed"):
            frappe.db.set_value("WAFD Loading Record", self.loading_record, {"status": "خرجت / Dispatched", "dispatch_time": self.actual_departure or now_datetime()}, update_modified=False)
        _sync_resource_statuses(self.vehicle, self.driver)

    def on_trash(self):
        if frappe.db.exists("WAFD Delivery Proof", {"delivery_trip": self.name}):
            frappe.throw("لا يمكن حذف رحلة لديها إثبات تسليم / Cannot delete a trip with delivery proof")
        vehicle, driver = self.vehicle, self.driver
        if self.loading_record:
            frappe.db.set_value("WAFD Loading Record", self.loading_record, "status", "تم التحميل / Loaded", update_modified=False)
        _sync_resource_statuses(vehicle, driver, exclude_trip=self.name)


def _sync_resource_statuses(vehicle, driver, exclude_trip=None):
    filters = {"status": ["in", ACTIVE]}
    if exclude_trip:
        filters["name"] = ["!=", exclude_trip]
    if vehicle and frappe.db.exists("WAFD Vehicle", vehicle):
        vf = dict(filters, vehicle=vehicle)
        frappe.db.set_value("WAFD Vehicle", vehicle, "status", "في مهمة / On Trip" if frappe.db.exists("WAFD Delivery Trip", vf) else "متاحة / Available", update_modified=False)
    if driver and frappe.db.exists("WAFD Driver", driver):
        df = dict(filters, driver=driver)
        frappe.db.set_value("WAFD Driver", driver, "status", "في مهمة / On Trip" if frappe.db.exists("WAFD Delivery Trip", df) else "متاح / Available", update_modified=False)
