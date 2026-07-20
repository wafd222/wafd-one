import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate


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
        # Preserve a manually agreed contract value. Only derive it when empty.
        if not flt(self.contract_value) and total_value:
            self.contract_value = total_value

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
    if not contract.services:
        frappe.throw("أضف خدمة أو وجبة واحدة على الأقل / Add at least one service or meal")
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
