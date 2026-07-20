import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class WAFDInvoice(Document):
    def validate(self):
        self._protect_invoice_with_confirmed_payments()
        if not self.invoice_date:
            self.invoice_date = nowdate()
        if self.due_date and getdate(self.due_date) < getdate(self.invoice_date):
            frappe.throw("تاريخ الاستحقاق لا يمكن أن يسبق تاريخ الفاتورة / Due date cannot precede invoice date")

        if self.billing_basis == "قيمة العقد / Contract Value":
            self.subtotal = flt(frappe.db.get_value("WAFD Catering Project", self.project, "contract_value"))
        elif self.billing_basis == "الكميات المسلمة / Delivered Quantities":
            # Build invoice items automatically from accepted, uninvoiced delivery proofs.
            # This keeps billing tied to actual delivered quantities and prevents manual
            # entry mistakes. Existing item rows are preserved and recalculated.
            if not self.items:
                self._populate_items_from_deliveries()
            self._recalculate_delivered_items()
            self.subtotal = sum(flt(row.amount) for row in (self.items or []))

        # Always calculate financial totals on the server. Client-side calculation is
        # only for immediate display; these values are the authoritative saved values.
        self.subtotal = flt(self.subtotal)
        self.tax_rate = flt(self.tax_rate)
        self.tax_amount = flt(self.subtotal * self.tax_rate / 100, 2)
        self.grand_total = flt(self.subtotal + self.tax_amount, 2)

        if self.billing_basis != "يدوي / Manual" and flt(self.grand_total) <= 0:
            frappe.throw(
                "لا يمكن حفظ فاتورة بقيمة صفر. حدد سعر الوحدة في خطة الوجبة أو خدمات المشروع، "
                "أو استخدم الفوترة اليدوية / Zero-value invoices are not allowed. Set a unit price "
                "in the meal plan or project services, or use manual billing."
            )

        confirmed = 0
        if not self.is_new():
            confirmed = frappe.db.sql(
                """select coalesce(sum(amount),0) from `tabWAFD Payment`
                   where invoice=%s and status='معتمد / Confirmed'""",
                self.name,
            )[0][0]
        self.paid_amount = flt(confirmed, 2)
        self.balance = max(flt(self.grand_total - self.paid_amount, 2), 0)
        self._set_status()


    def _protect_invoice_with_confirmed_payments(self):
        if self.is_new():
            return
        confirmed = frappe.db.count("WAFD Payment", {"invoice": self.name, "status": "معتمد / Confirmed"})
        if not confirmed:
            return
        previous = self.get_doc_before_save()
        if not previous:
            return
        protected = ("project", "invoice_date", "billing_basis", "subtotal", "tax_rate")
        changed = [self.meta.get_label(field) for field in protected if self.get(field) != previous.get(field)]
        old_items = [(r.meal_plan, flt(r.delivered_quantity), flt(r.unit_price), flt(r.amount)) for r in (previous.items or [])]
        new_items = [(r.meal_plan, flt(r.delivered_quantity), flt(r.unit_price), flt(r.amount)) for r in (self.items or [])]
        if old_items != new_items:
            changed.append(self.meta.get_label("items"))
        if changed:
            frappe.throw(
                "لا يمكن تعديل أساس أو قيمة فاتورة عليها تحصيلات معتمدة: {0} / Billing fields cannot be changed after confirmed payments: {0}".format(
                    ", ".join(changed)
                )
            )

    def _populate_items_from_deliveries(self):
        from wafd_one.finance import _append_delivery_rows, _get_billable_delivery_rows

        rows = _get_billable_delivery_rows(
            self.project, exclude_invoice=None if self.is_new() else self.name
        )
        if not rows:
            frappe.throw(
                "لا توجد كميات تسليم مقبولة وغير مفوترة لهذا المشروع / "
                "No accepted, uninvoiced delivery quantities are available for this project"
            )
        _append_delivery_rows(self, rows)

    def _recalculate_delivered_items(self):
        from wafd_one.finance import _get_billable_delivery_rows, resolve_unit_price

        if not self.items:
            frappe.throw(
                "لا توجد كميات تسليم مقبولة وغير مفوترة لهذا المشروع / "
                "No accepted, uninvoiced delivery quantities are available for this project"
            )

        available_rows = _get_billable_delivery_rows(
            self.project, exclude_invoice=None if self.is_new() else self.name
        )
        available_by_plan = {row.name: flt(row.delivered_quantity) for row in available_rows}
        seen_plans = set()
        missing = []

        for row in self.items:
            if not row.meal_plan:
                frappe.throw("يجب تحديد خطة الوجبة لكل بند / Every invoice item must have a meal plan")
            if row.meal_plan in seen_plans:
                frappe.throw(
                    "لا يمكن تكرار خطة الوجبة في الفاتورة: {0} / Duplicate meal plan in invoice: {0}".format(
                        row.meal_plan
                    )
                )
            seen_plans.add(row.meal_plan)

            plan_project = frappe.db.get_value("WAFD Meal Plan", row.meal_plan, "project")
            if plan_project != self.project:
                frappe.throw(
                    "خطة الوجبة {0} لا تتبع هذا المشروع / Meal plan {0} does not belong to this project".format(
                        row.meal_plan
                    )
                )

            row.delivered_quantity = flt(row.delivered_quantity)
            if row.delivered_quantity <= 0:
                frappe.throw("كمية البند يجب أن تكون أكبر من صفر / Invoice item quantity must be greater than zero")

            available = available_by_plan.get(row.meal_plan, 0)
            if row.delivered_quantity > available:
                frappe.throw(
                    "الكمية المفوترة لخطة الوجبة {0} ({1}) تتجاوز الكمية المتاحة للفوترة ({2}) / "
                    "Invoiced quantity for meal plan {0} ({1}) exceeds the billable quantity ({2})".format(
                        row.meal_plan, row.delivered_quantity, available
                    )
                )

            row.unit_price = flt(row.unit_price) or resolve_unit_price(
                self.project, row.meal_plan, row.meal_type
            )
            if row.unit_price <= 0:
                missing.append(row.meal_plan or str(row.idx))
            row.amount = flt(row.delivered_quantity * row.unit_price, 2)

        if missing:
            frappe.throw(
                "تعذر تحديد سعر الوحدة للبنود: {0} / Unable to resolve unit price for items: {0}".format(
                    ", ".join(missing)
                )
            )

    def _set_status(self):
        from wafd_one.governance import ensure_approved
        if self.status == "مرسلة / Sent" and not self.is_new():
            previous = self.get_doc_before_save()
            if previous and previous.status != self.status:
                ensure_approved(self, "إرسال الفاتورة / invoice sending")
        if self.status == "ملغاة / Cancelled":
            return
        if flt(self.grand_total) <= 0:
            self.status = "مسودة / Draft"
        elif self.balance <= 0:
            self.status = "مدفوعة / Paid"
        elif self.paid_amount > 0:
            self.status = "مدفوعة جزئياً / Partially Paid"
        elif self.due_date and getdate(self.due_date) < getdate(nowdate()):
            self.status = "متأخرة / Overdue"
        elif self.status not in ("مسودة / Draft", "مرسلة / Sent"):
            self.status = "مرسلة / Sent"

    def on_update(self):
        from wafd_one.finance import refresh_project_financials
        refresh_project_financials(self.project)

    def on_trash(self):
        if frappe.db.exists("WAFD Payment", {"invoice": self.name, "status": "معتمد / Confirmed"}):
            frappe.throw("لا يمكن حذف فاتورة مرتبطة بتحصيل معتمد / An invoice with confirmed payments cannot be deleted")
