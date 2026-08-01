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
        # Older deployments may retain a stale Custom Field/Property Setter
        # that writes the grand total into advance_percent on a brand-new
        # contract. Normalize only new documents; existing saved contracts
        # still receive strict validation below.
        if self.is_new() and flt(self.advance_percent) > 100:
            self.advance_percent = 0

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

# Transaction parents linked to a contract/project, ordered from the end of the
# workflow back to the project. Child rows are removed by Frappe with parents.
_PURGE_ORDER = [
    "WAFD Payment",
    "WAFD Invoice",
    "WAFD Receiving Note",
    "WAFD Delivery Note",
    "WAFD Delivery Proof",
    "WAFD Complaint",
    "WAFD Hotel Undertaking",
    "WAFD Delivery Trip",
    "WAFD Loading Record",
    "WAFD Packaging Record",
    "WAFD Quality Inspection",
    # Reverse and remove stock before deleting production documents.
    "WAFD Stock Movement",
    "WAFD Production Batch",
    "WAFD Purchase Order",
    "WAFD Procurement Plan",
    "WAFD Project Revenue",
    "WAFD Project Cost",
    "WAFD Cost Snapshot",
    "WAFD Operations Alert",
    "WAFD Daily Meal Plan",
    "WAFD Meal Plan",
]


def _check_contract_purge_permission():
    user = frappe.session.user
    roles = set(frappe.get_roles(user))
    if user != "Administrator" and "System Manager" not in roles:
        frappe.throw(
            "حذف العقد بالكامل متاح فقط لمدير النظام / Only Administrator or System Manager can permanently purge a contract",
            frappe.PermissionError,
        )


def _linked_names(doctype, contract_name, project_name=None):
    if not frappe.db.exists("DocType", doctype):
        return []
    meta = frappe.get_meta(doctype)
    filters = []
    values = []
    if meta.has_field("contract"):
        filters.append("contract=%s")
        values.append(contract_name)
    if project_name and meta.has_field("project"):
        filters.append("project=%s")
        values.append(project_name)
    if not filters:
        return []
    order_by = ""
    if doctype == "WAFD Stock Movement":
        # Reverse ledger-affecting documents newest first, exactly like undoing
        # a stack of transactions. This is required to restore quantities and
        # weighted-average valuation correctly.
        order_by = " order by posting_date desc, creation desc"
    return frappe.db.sql_list(
        f"select name from `tab{doctype}` where " + " or ".join(filters) + order_by,
        tuple(values),
    )


def _discover_contract_stock_movements(records, project_name=None):
    """Discover the complete stock chain belonging to one contract workflow.

    Legacy movements are not always populated with ``project``.  They can still
    belong to the contract through ``production_batch`` or a reference to any
    linked operational document.  Build a closure so same-contract Issue/Waste/
    Transfer movements are reversed automatically before older Receipts.
    """
    if not frappe.db.exists("DocType", "WAFD Stock Movement"):
        return []

    discovered = set(records.get("WAFD Stock Movement", []) or [])
    batch_names = set(records.get("WAFD Production Batch", []) or [])
    reference_names = set()
    for doctype, names in records.items():
        if doctype not in ("WAFD Contract", "WAFD Catering Project"):
            reference_names.update(names or [])
    if project_name:
        reference_names.add(project_name)

    # Repeat because a newly discovered movement may itself be referenced by a
    # later corrective/transfer movement.
    for _ in range(8):
        clauses = []
        values = []
        if project_name:
            clauses.append("project=%s")
            values.append(project_name)
        if batch_names:
            marks = ",".join(["%s"] * len(batch_names))
            clauses.append(f"production_batch in ({marks})")
            values.extend(sorted(batch_names))
        all_refs = reference_names | discovered
        if all_refs:
            marks = ",".join(["%s"] * len(all_refs))
            clauses.append(f"reference_name in ({marks})")
            values.extend(sorted(all_refs))
        if not clauses:
            break
        rows = frappe.db.sql_list(
            "select name from `tabWAFD Stock Movement` where " + " or ".join(clauses),
            tuple(values),
        )
        before = len(discovered)
        discovered.update(rows)
        if len(discovered) == before:
            break

    if not discovered:
        return []
    marks = ",".join(["%s"] * len(discovered))
    return frappe.db.sql_list(
        f"select name from `tabWAFD Stock Movement` where name in ({marks}) "
        "order by posting_date desc, creation desc",
        tuple(sorted(discovered)),
    )


def _contract_purge_plan(contract_name):
    contract = frappe.get_doc("WAFD Contract", contract_name)
    project_name = contract.project or frappe.db.get_value(
        "WAFD Catering Project", {"contract": contract_name}, "name"
    )
    records = {}
    for doctype in _PURGE_ORDER:
        names = _linked_names(doctype, contract_name, project_name)
        if names:
            records[doctype] = names

    # Replace the project-only result with the full workflow stock closure.
    stock_names = _discover_contract_stock_movements(records, project_name)
    if stock_names:
        records["WAFD Stock Movement"] = stock_names

    if project_name:
        records["WAFD Catering Project"] = [project_name]
    records["WAFD Contract"] = [contract_name]
    return contract, project_name, records



def _stock_reversal_preflight(records):
    """Simulate the complete linked stock rollback without changing data.

    The simulation runs movements newest-first, exactly like the real cleanup.
    This means a later Issue/Waste/Transfer belonging to the same contract is
    automatically restored in the virtual balance before an older Receipt is
    checked. Only shortages caused by records outside the cleanup chain (or
    reserved stock / legacy adjustments) remain blockers.
    """
    from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import _get_balance

    movement_names = records.get("WAFD Stock Movement", [])
    virtual = {}
    diagnostics = []
    blockers = []
    automatic = []

    def state(warehouse, row):
        key = (warehouse, row.ingredient)
        if key not in virtual:
            balance = _get_balance(warehouse, row.ingredient, row.uom)
            virtual[key] = {
                "quantity": flt(balance.actual_quantity),
                "reserved": flt(balance.reserved_quantity),
                "initial": flt(balance.actual_quantity),
            }
        return key, virtual[key]

    for name in movement_names:
        if not frappe.db.exists("WAFD Stock Movement", name):
            continue
        doc = frappe.get_doc("WAFD Stock Movement", name)
        result = {"name": name, "safe": True, "blockers": [], "items": []}
        if doc.status != "مرحلة / Posted":
            diagnostics.append(result)
            continue
        if doc.movement_type == "تسوية / Adjustment":
            blocker = {
                "movement": name,
                "reason": "adjustment",
                "message": "حركة تسوية لا تحتوي على رصيد ما قبل التسوية / Adjustment movement has no stored pre-adjustment balance",
            }
            result["safe"] = False
            result["blockers"].append(blocker)
            blockers.append(blocker)
            diagnostics.append(result)
            continue

        for row in doc.items or []:
            qty = flt(row.quantity)
            item = {"movement": name, "ingredient": row.ingredient, "quantity": qty, "movement_type": doc.movement_type}

            if doc.movement_type in ("صرف / Issue", "هالك / Waste"):
                key, st = state(doc.source_warehouse, row)
                before = st["quantity"]
                st["quantity"] += qty
                item.update({"warehouse": doc.source_warehouse, "action": "restore", "before": before, "after": st["quantity"]})
                automatic.append(item.copy())

            elif doc.movement_type == "استلام / Receipt":
                key, st = state(doc.target_warehouse, row)
                before = st["quantity"]
                after = before - qty
                item.update({"warehouse": doc.target_warehouse, "action": "remove_receipt", "before": before, "after": after, "reserved_quantity": st["reserved"]})
                if after < -0.000001 or after + 0.000001 < st["reserved"]:
                    blocker = dict(item)
                    blocker.update({
                        "required_quantity": qty,
                        "current_quantity": before,
                        "shortage": max(-after, 0),
                        "reserved_block": max(st["reserved"] - after, 0),
                        "dependencies": [],
                    })
                    result["safe"] = False
                    result["blockers"].append(blocker)
                    blockers.append(blocker)
                else:
                    st["quantity"] = max(after, 0)
                    automatic.append(item.copy())

            elif doc.movement_type == "تحويل / Transfer":
                target_key, target = state(doc.target_warehouse, row)
                target_before = target["quantity"]
                target_after = target_before - qty
                item.update({"warehouse": doc.target_warehouse, "source_warehouse": doc.source_warehouse, "action": "reverse_transfer", "before": target_before, "after": target_after, "reserved_quantity": target["reserved"]})
                if target_after < -0.000001 or target_after + 0.000001 < target["reserved"]:
                    blocker = dict(item)
                    blocker.update({
                        "required_quantity": qty,
                        "current_quantity": target_before,
                        "shortage": max(-target_after, 0),
                        "reserved_block": max(target["reserved"] - target_after, 0),
                        "dependencies": [],
                    })
                    result["safe"] = False
                    result["blockers"].append(blocker)
                    blockers.append(blocker)
                else:
                    target["quantity"] = max(target_after, 0)
                    source_key, source = state(doc.source_warehouse, row)
                    source_before = source["quantity"]
                    source["quantity"] += qty
                    item["source_before"] = source_before
                    item["source_after"] = source["quantity"]
                    automatic.append(item.copy())

            result["items"].append(item)
        diagnostics.append(result)

    # Attach likely external consumers only for genuine remaining blockers.
    cleanup_set = set(movement_names)
    for blocker in blockers:
        if not blocker.get("ingredient") or not blocker.get("warehouse"):
            continue
        later = frappe.db.sql(
            """select distinct sm.name, sm.movement_type, sm.posting_date, sm.project, sm.production_batch,
                        sm.reference_type, sm.reference_name
                 from `tabWAFD Stock Movement` sm
                 join `tabWAFD Stock Movement Item` i on i.parent=sm.name
                where sm.status='مرحلة / Posted' and i.ingredient=%s
                  and sm.source_warehouse=%s
                order by sm.posting_date desc, sm.creation desc limit 30""",
            (blocker["ingredient"], blocker["warehouse"]), as_dict=True,
        )
        blocker["dependencies"] = [row for row in later if row.name not in cleanup_set]

    balance_effects = []
    for (warehouse, ingredient), st in virtual.items():
        change = flt(st["quantity"]) - flt(st["initial"])
        if abs(change) > 0.000001:
            balance_effects.append({
                "warehouse": warehouse,
                "ingredient": ingredient,
                "before": st["initial"],
                "after": st["quantity"],
                "change": change,
                "reserved_quantity": st["reserved"],
            })

    return {
        "safe": not blockers,
        "diagnostics": diagnostics,
        "blockers": blockers,
        "automatic_actions": automatic,
        "balance_effects": balance_effects,
    }

@frappe.whitelist()
def preview_contract_purge(contract_name):
    """Preview exactly what the one-click test-contract purge will remove."""
    _check_contract_purge_permission()
    contract, project_name, records = _contract_purge_plan(contract_name)
    stock_analysis = _stock_reversal_preflight(records)
    return {
        "contract": contract.name,
        "title": contract.contract_title,
        "project": project_name,
        "counts": {doctype: len(names) for doctype, names in records.items()},
        "total": sum(len(names) for names in records.values()),
        "confirmation_phrase": "DELETE",
        "stock_analysis": stock_analysis,
    }


def _prepare_and_delete(doctype, name, reason=None):
    if not frappe.db.exists(doctype, name):
        return {"stock_reversed": 0, "stock_items": 0}
    doc = frappe.get_doc(doctype, name)
    reversal = {"stock_reversed": 0, "stock_items": 0}

    # WAFD Stock Movement uses its own posting state rather than docstatus.
    # Reverse its quantities and valuation before deletion; never bypass this.
    if doctype == "WAFD Stock Movement" and doc.get("status") == "مرحلة / Posted":
        from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import reverse_posted_movement
        result = reverse_posted_movement(doc, reason=reason)
        reversal["stock_reversed"] = 1 if result.get("reversed") else 0
        reversal["stock_items"] = result.get("items", 0)
        doc.reload()

    # Submitted WAFD documents must be cancelled first so their normal reversal
    # hooks run. Legacy payments from pre-RC56 are normalized defensively.
    if doc.docstatus == 1:
        doc.cancel()
    elif doctype == "WAFD Payment" and doc.get("status") == "معتمد / Confirmed":
        frappe.db.set_value(doctype, name, "status", "ملغي / Cancelled", update_modified=False)

    frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
    return reversal


@frappe.whitelist(methods=["POST"])
def purge_contract_and_operations(contract_name, confirmation=""):
    """Permanently delete one contract and only its linked operational chain."""
    _check_contract_purge_permission()
    if (confirmation or "").strip().upper() != "DELETE":
        frappe.throw("اكتب DELETE للتأكيد / Type DELETE to confirm")

    contract, project_name, records = _contract_purge_plan(contract_name)
    stock_analysis = _stock_reversal_preflight(records)
    if not stock_analysis["safe"]:
        frappe.throw(
            "تعذر تنفيذ الحذف لأن بعض حركات المخزون لا يمكن عكسها بأمان. افتح معاينة الحذف لمعرفة الأصناف والحركات التابعة. "
            "/ Contract deletion blocked by unsafe stock reversals. Review the deletion preview for details."
        )

    # Break the intentional Contract <-> Project circular link before deletion.
    frappe.db.set_value("WAFD Contract", contract.name, "project", None, update_modified=False)
    if project_name and frappe.db.exists("WAFD Catering Project", project_name):
        frappe.db.set_value("WAFD Catering Project", project_name, "contract", None, update_modified=False)

    deleted = {}
    stock_reversed = 0
    stock_items = 0
    for doctype in _PURGE_ORDER:
        names = records.get(doctype, [])
        for name in names:
            result = _prepare_and_delete(doctype, name, reason=f"contract purge {contract.name}")
            stock_reversed += result.get("stock_reversed", 0)
            stock_items += result.get("stock_items", 0)
        if names:
            deleted[doctype] = len(names)

    if project_name and frappe.db.exists("WAFD Catering Project", project_name):
        _prepare_and_delete("WAFD Catering Project", project_name)
        deleted["WAFD Catering Project"] = 1

    _prepare_and_delete("WAFD Contract", contract.name)
    deleted["WAFD Contract"] = 1

    frappe.logger("wafd_one").warning(
        "Permanent contract purge by %s: %s (%s)",
        frappe.session.user,
        contract_name,
        deleted,
    )
    return {
        "deleted": deleted,
        "total": sum(deleted.values()),
        "stock_movements_reversed": stock_reversed,
        "stock_items_reversed": stock_items,
        "stock_balance_effects": stock_analysis.get("balance_effects") or [],
        "automatic_stock_actions": len(stock_analysis.get("automatic_actions") or []),
    }


@frappe.whitelist(methods=["POST"])
def reset_contract_test_data(contract_name, confirmation=""):
    """Delete the linked test-operation chain while preserving the contract.

    The request is transactional: any failure rolls the complete reset back.
    The contract is returned to Draft with its project link cleared, ready for
    a fresh end-to-end test run.
    """
    _check_contract_purge_permission()
    if (confirmation or "").strip().upper() != "RESET":
        frappe.throw("اكتب RESET للتأكيد / Type RESET to confirm")

    contract, project_name, records = _contract_purge_plan(contract_name)
    stock_analysis = _stock_reversal_preflight(records)
    if not stock_analysis["safe"]:
        frappe.throw(
            "تعذرت إعادة التهيئة لأن بعض حركات المخزون لا يمكن عكسها بأمان. افتح المعاينة لمعرفة الأصناف والحركات التابعة. "
            "/ Contract reset blocked by unsafe stock reversals. Review the preview for details."
        )

    # Break the Contract <-> Project circular link before deleting the chain.
    frappe.db.set_value("WAFD Contract", contract.name, "project", None, update_modified=False)
    if project_name and frappe.db.exists("WAFD Catering Project", project_name):
        frappe.db.set_value("WAFD Catering Project", project_name, "contract", None, update_modified=False)

    deleted = {}
    stock_reversed = 0
    stock_items = 0
    for doctype in _PURGE_ORDER:
        names = records.get(doctype, [])
        for name in names:
            result = _prepare_and_delete(doctype, name, reason=f"contract reset {contract.name}")
            stock_reversed += result.get("stock_reversed", 0)
            stock_items += result.get("stock_items", 0)
        if names:
            deleted[doctype] = len(names)

    if project_name and frappe.db.exists("WAFD Catering Project", project_name):
        _prepare_and_delete("WAFD Catering Project", project_name)
        deleted["WAFD Catering Project"] = 1

    # Preserve the contract itself and make it ready for a clean regeneration.
    frappe.db.set_value(
        "WAFD Contract",
        contract.name,
        {"project": None, "status": "مسودة / Draft"},
        update_modified=True,
    )

    frappe.logger("wafd_one").warning(
        "Contract test data reset by %s: %s (%s)",
        frappe.session.user,
        contract_name,
        deleted,
    )
    return {
        "deleted": deleted,
        "total": sum(deleted.values()),
        "contract": contract.name,
        "stock_movements_reversed": stock_reversed,
        "stock_items_reversed": stock_items,
        "stock_balance_effects": stock_analysis.get("balance_effects") or [],
        "automatic_stock_actions": len(stock_analysis.get("automatic_actions") or []),
    }
