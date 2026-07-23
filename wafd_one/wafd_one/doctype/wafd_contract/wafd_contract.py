import frappe
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt, getdate


class WAFDContract(Document):
    def validate(self):
        self._validate_core_fields()
        self._calculate_services()
        self._validate_linked_project()

    def on_update(self):
        self._sync_linked_project()

    def _validate_core_fields(self):
        if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw("تاريخ نهاية العقد يجب أن يكون بعد تاريخ البداية / Contract end date must be after start date")
        if self.contract_value is not None and flt(self.contract_value) < 0:
            frappe.throw("قيمة العقد لا يمكن أن تكون سالبة / Contract value cannot be negative")
        if self.beneficiary_count is not None and cint(self.beneficiary_count) < 0:
            frappe.throw("عدد المستفيدين لا يمكن أن يكون سالبًا / Beneficiary count cannot be negative")
        for fieldname in ("beneficiary_count", "vip_count", "children_count", "payment_due_days"):
            if self.get(fieldname) is not None and cint(self.get(fieldname)) < 0:
                frappe.throw(f"{self.meta.get_label(fieldname)} لا يمكن أن يكون سالبًا / Cannot be negative")
        for fieldname in ("discount_amount", "tax_rate", "advance_percent"):
            if self.get(fieldname) is not None and flt(self.get(fieldname)) < 0:
                frappe.throw(f"{self.meta.get_label(fieldname)} لا يمكن أن يكون سالبًا / Cannot be negative")
        if flt(self.tax_rate) > 100 or flt(self.advance_percent) > 100:
            frappe.throw("النسب المئوية لا يمكن أن تتجاوز 100% / Percentages cannot exceed 100%")
        if self.start_date and self.end_date:
            self.duration_days = date_diff(self.end_date, self.start_date) + 1
        else:
            self.duration_days = 0
        if self.status == "ساري / Active":
            from wafd_one.governance import ensure_approved
            if not self.is_new():
                previous = self.get_doc_before_save()
                if previous and previous.status != self.status:
                    ensure_approved(self, "تفعيل العقد / contract activation")
            missing=[]
            for fieldname in ("mission","start_date","end_date","beneficiary_count"):
                if not self.get(fieldname): missing.append(self.meta.get_label(fieldname))
            if missing:
                frappe.throw("لا يمكن تفعيل العقد قبل استكمال: {0} / Complete required operational data before activation".format(", ".join(missing)))

    def _calculate_services(self):
        total_value = 0
        for row in self.get("services") or []:
            start = getdate(row.service_start_date or self.start_date) if (row.service_start_date or self.start_date) else None
            end = getdate(row.service_end_date or self.end_date) if (row.service_end_date or self.end_date) else None
            if start and end and end < start:
                frappe.throw(f"تاريخ خدمة غير صحيح في الصف {row.idx} / Invalid service dates in row {row.idx}")
            days = cint(row.service_days)
            if not days and start and end:
                days = (end - start).days + 1
                row.service_days = days
            beneficiaries = cint(row.beneficiaries) or cint(self.beneficiary_count)
            multiplier = flt(row.meals_per_person_per_day) or 1
            row.total_meals = cint(days * beneficiaries * multiplier)
            row.estimated_revenue = flt(row.total_meals) * flt(row.unit_price)
            total_value += flt(row.estimated_revenue)
        self.services_subtotal = total_value
        # Contract Value is the agreed amount before VAT. When it is empty, use
        # the services subtotal. This makes manual contracts and itemised
        # contracts follow the same financial rule.
        if not flt(self.contract_value) and total_value:
            self.contract_value = total_value
        taxable = max(flt(self.contract_value) - flt(self.discount_amount), 0)
        self.tax_amount = taxable * flt(self.tax_rate) / 100
        self.grand_total = taxable + flt(self.tax_amount)
        self.advance_amount = flt(self.grand_total) * flt(self.advance_percent) / 100
        self.outstanding_contract_amount = max(flt(self.grand_total) - flt(self.advance_amount), 0)

    def _validate_linked_project(self):
        if not self.project:
            return
        project = frappe.get_doc("WAFD Catering Project", self.project)
        if project.contract and project.contract != self.name:
            frappe.throw("المشروع مرتبط بعقد آخر / Project is linked to another contract")
        if self.mission and project.mission and project.mission != self.mission:
            frappe.throw("العميل في العقد لا يطابق العميل في المشروع / Contract mission does not match project mission")

    def _sync_linked_project(self):
        if not self.project:
            return
        project = frappe.get_doc("WAFD Catering Project", self.project)
        changed = False
        mapping = {
            "contract": self.name,
            "mission": self.mission,
            "project_type": self.project_type or "إعاشة فندقية / Hotel Catering",
            "start_date": self.start_date,
            "end_date": self.end_date,
            "beneficiary_count": self.beneficiary_count,
            "contract_value": self.contract_value,
            "currency": self.currency,
            "primary_hotel": self.hotel,
            "default_source_warehouse": self.default_source_warehouse,
            "default_vehicle": self.default_vehicle,
            "default_driver": self.default_driver,
            "contract_type": self.contract_type,
            "service_model": self.service_model,
            "first_meal": self.first_meal,
            "last_meal": self.last_meal,
            "vip_count": self.vip_count,
            "children_count": self.children_count,
            "delivery_location": self.delivery_location,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "delivery_window": self.delivery_window,
            "delivery_instructions": self.delivery_instructions,
            "project_manager": self.project_manager,
            "operations_manager": self.operations_manager,
            "delivery_supervisor": self.delivery_supervisor,
            "default_kitchen": self.default_kitchen,
            "operation_priority": self.operation_priority,
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "grand_total": self.grand_total,
            "discount_amount": self.discount_amount,
            "advance_amount": self.advance_amount,
        }
        for fieldname, value in mapping.items():
            if value not in (None, "") and project.get(fieldname) != value:
                project.set(fieldname, value)
                changed = True
        if self.hotel:
            rows = [row for row in (project.hotels or []) if row.hotel == self.hotel]
            if not rows:
                project.append("hotels", {"hotel": self.hotel, "guest_count": self.beneficiary_count or 0})
                changed = True
            elif self.beneficiary_count and rows[0].guest_count != self.beneficiary_count:
                rows[0].guest_count = self.beneficiary_count
                changed = True
        # Services are copied only while the project has no operation plan. This
        # prevents an edited contract from silently rewriting live production.
        if self.services and not project.services and not frappe.db.exists("WAFD Meal Plan", {"project": project.name}):
            for row in self.services:
                project.append("services", _service_values(row))
            changed = True
        if changed:
            project.flags.from_contract_sync = True
            project.save(ignore_permissions=True)


def _service_values(row):
    return {
        "service_type": row.service_type,
        "meal_name": row.meal_name,
        "service_time": row.service_time,
        "delivery_lead_minutes": row.delivery_lead_minutes,
        "packaging_type": row.packaging_type,
        "recipe": row.recipe,
        "service_start_date": row.service_start_date,
        "service_end_date": row.service_end_date,
        "service_days": row.service_days,
        "beneficiaries": row.beneficiaries,
        "meals_per_person_per_day": row.meals_per_person_per_day,
        "total_meals": row.total_meals,
        "unit_price": row.unit_price,
        "estimated_revenue": row.estimated_revenue,
        "notes": row.notes,
    }


@frappe.whitelist()
def create_project_from_contract(contract_name):
    contract = frappe.get_doc("WAFD Contract", contract_name)
    contract.check_permission("write")
    if contract.project:
        return {"name": contract.project, "created": False}
    if not contract.mission:
        frappe.throw("حدد البعثة أو العميل أولاً / Select the mission or customer first")
    if not contract.start_date or not contract.end_date:
        frappe.throw("حدد تاريخ بداية ونهاية العقد / Set contract start and end dates")
    if not contract.hotel:
        frappe.throw("حدد الفندق الرئيسي قبل إنشاء المشروع / Select the primary hotel before creating the project")

    project = frappe.get_doc({
        "doctype": "WAFD Catering Project",
        "naming_series": "WAFD-PROJ-.#####",
        "project_name": contract.contract_title,
        "mission": contract.mission,
        "contract": contract.name,
        "project_type": contract.project_type or "إعاشة فندقية / Hotel Catering",
        "primary_hotel": contract.hotel,
        "start_date": contract.start_date,
        "end_date": contract.end_date,
        "beneficiary_count": contract.beneficiary_count,
        "contract_value": contract.contract_value,
        "currency": contract.currency or "SAR",
        "default_source_warehouse": contract.default_source_warehouse,
        "default_vehicle": contract.default_vehicle,
        "default_driver": contract.default_driver,
        "contract_type": contract.contract_type,
        "service_model": contract.service_model,
        "first_meal": contract.first_meal,
        "last_meal": contract.last_meal,
        "vip_count": contract.vip_count,
        "children_count": contract.children_count,
        "delivery_location": contract.delivery_location,
        "contact_person": contract.contact_person,
        "contact_phone": contract.contact_phone,
        "delivery_window": contract.delivery_window,
        "delivery_instructions": contract.delivery_instructions,
        "project_manager": contract.project_manager,
        "operations_manager": contract.operations_manager,
        "delivery_supervisor": contract.delivery_supervisor,
        "default_kitchen": contract.default_kitchen,
        "operation_priority": contract.operation_priority,
        "tax_rate": contract.tax_rate,
        "tax_amount": contract.tax_amount,
        "grand_total": contract.grand_total,
        "discount_amount": contract.discount_amount,
        "advance_amount": contract.advance_amount,
        "status": "مسودة / Draft",
    })
    if contract.hotel:
        project.append("hotels", {"hotel": contract.hotel, "guest_count": contract.beneficiary_count or 0})
    for row in contract.services or []:
        project.append("services", _service_values(row))
    project.insert()
    contract.db_set("project", project.name, update_modified=True)
    return {"name": project.name, "created": True}


@frappe.whitelist()
def activate_and_generate_operations(contract_name):
    """Safely activate a contract, create its project and generate the operation plan.

    The endpoint is idempotent: repeated calls reuse the existing project, meal
    plans and production batches instead of creating duplicates.
    """
    contract = frappe.get_doc("WAFD Contract", contract_name)
    contract.check_permission("write")
    if contract.status == "ملغي / Cancelled":
        frappe.throw("لا يمكن تشغيل عقد ملغي / A cancelled contract cannot be activated")
    contract.status = "ساري / Active"
    contract.save()
    project_result = create_project_from_contract(contract.name)
    from wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project import generate_operation_plan
    operation_result = generate_operation_plan(project_result["name"])
    return {"project": project_result, "operations": operation_result}
