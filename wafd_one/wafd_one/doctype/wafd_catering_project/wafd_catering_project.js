frappe.ui.form.on("WAFD Catering Project", {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__("Generate Meal Plans"), () => {
            frappe.confirm(
                __("Generate daily meal plans from project services and hotels?"),
                () => frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project.generate_meal_plans",
                    args: { project_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Generating meal plans..."),
                    callback(r) {
                        const result = r.message || {};
                        frappe.msgprint(__("Created {0} meal plans; skipped {1} existing plans.", [result.created || 0, result.skipped || 0]));
                    }
                })
            );
        }, __("Operations"));
        frm.add_custom_button(__("Meal Plan"), () => frappe.new_doc("WAFD Meal Plan", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Delivery Trip"), () => frappe.new_doc("WAFD Delivery Trip", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Project Cost"), () => frappe.new_doc("WAFD Project Cost", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Project Revenue"), () => frappe.new_doc("WAFD Project Revenue", { project: frm.doc.name }), __("Create"));
    }
});

frappe.ui.form.on("WAFD Project Service", {
    service_days: recalculate,
    beneficiaries: recalculate,
    meals_per_person_per_day: recalculate,
    unit_price: recalculate
});

function recalculate(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const days = flt(row.service_days || frm.doc.duration_days || 1);
    const beneficiaries = flt(row.beneficiaries || frm.doc.beneficiary_count || 0);
    const multiplier = flt(row.meals_per_person_per_day || 1);
    const total = Math.round(days * beneficiaries * multiplier);
    frappe.model.set_value(cdt, cdn, "total_meals", total);
    frappe.model.set_value(cdt, cdn, "estimated_revenue", total * flt(row.unit_price));
}
