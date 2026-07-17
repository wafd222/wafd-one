import frappe
from frappe.model.document import Document
from frappe.utils import cint


class WAFDContract(Document):
    def validate(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw("تاريخ نهاية العقد يجب أن يكون بعد تاريخ البداية / Contract end date must be after start date")
        if self.contract_value is not None and self.contract_value < 0:
            frappe.throw("قيمة العقد لا يمكن أن تكون سالبة / Contract value cannot be negative")
        if self.beneficiary_count is not None and cint(self.beneficiary_count) < 0:
            frappe.throw("عدد المستفيدين لا يمكن أن يكون سالبًا / Beneficiary count cannot be negative")
        self._validate_linked_project()

    def on_update(self):
        self._sync_linked_project()

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
            "start_date": self.start_date,
            "end_date": self.end_date,
            "beneficiary_count": self.beneficiary_count,
            "contract_value": self.contract_value,
            "currency": self.currency,
        }
        for fieldname, value in mapping.items():
            if value not in (None, "") and project.get(fieldname) != value:
                project.set(fieldname, value)
                changed = True
        if changed:
            project.flags.from_contract_sync = True
            project.save(ignore_permissions=True)


@frappe.whitelist()
def create_project_from_contract(contract_name):
    contract = frappe.get_doc("WAFD Contract", contract_name)
    contract.check_permission("write")
    if contract.project:
        return {"name": contract.project, "created": False}

    project = frappe.get_doc({
        "doctype": "WAFD Catering Project",
        "project_name": contract.contract_title,
        "mission": contract.mission,
        "contract": contract.name,
        "start_date": contract.start_date,
        "end_date": contract.end_date,
        "beneficiary_count": contract.beneficiary_count,
        "contract_value": contract.contract_value,
        "currency": contract.currency or "SAR",
        "status": "مسودة / Draft",
    })
    project.insert()
    contract.db_set("project", project.name, update_modified=True)
    return {"name": project.name, "created": True}
