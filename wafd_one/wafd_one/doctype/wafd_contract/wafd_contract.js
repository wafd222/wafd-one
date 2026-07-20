frappe.ui.form.on("WAFD Contract", {
    refresh(frm) {
        if (frm.is_new()) return;

        if (!frm.doc.project) {
            frm.add_custom_button(__("إنشاء المشروع / Create Project"), () => {
                frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.create_project_from_contract",
                    args: { contract_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("جارٍ إنشاء المشروع..."),
                    callback(r) {
                        if (r.message?.name) frappe.set_route("Form", "WAFD Catering Project", r.message.name);
                    }
                });
            }, __("التشغيل / Operations"));
        }

        frm.add_custom_button(__("تفعيل وبناء خطة التشغيل / Activate & Build Operations"), () => {
            frappe.confirm(
                __("سيتم تفعيل العقد وإنشاء المشروع وخطط الوجبات ودفعات الإنتاج بدون تكرار السجلات. متابعة؟"),
                () => frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.activate_and_generate_operations",
                    args: { contract_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("جارٍ بناء دورة التشغيل..."),
                    callback(r) {
                        const data = r.message || {};
                        const op = data.operations || {};
                        frappe.msgprint({
                            title: __("تم إنشاء دورة التشغيل"),
                            indicator: (op.warnings || []).length ? "orange" : "green",
                            message: __("المشروع: {0}<br>خطط الوجبات الجديدة: {1}<br>دفعات الإنتاج الجديدة: {2}", [
                                data.project?.name || frm.doc.project || "-",
                                op.meal_plans_created || 0,
                                op.batches_created || 0
                            ])
                        });
                        frm.reload_doc();
                    }
                })
            );
        }, __("التشغيل / Operations"));
    }
});

frappe.ui.form.on("WAFD Project Service", {
    service_start_date: calculate_service,
    service_end_date: calculate_service,
    service_days: calculate_service,
    beneficiaries: calculate_service,
    meals_per_person_per_day: calculate_service,
    unit_price: calculate_service
});

function calculate_service(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const days = flt(row.service_days || 0);
    const beneficiaries = flt(row.beneficiaries || frm.doc.beneficiary_count || 0);
    const multiplier = flt(row.meals_per_person_per_day || 1);
    const total = Math.round(days * beneficiaries * multiplier);
    frappe.model.set_value(cdt, cdn, "total_meals", total);
    frappe.model.set_value(cdt, cdn, "estimated_revenue", total * flt(row.unit_price));
}
