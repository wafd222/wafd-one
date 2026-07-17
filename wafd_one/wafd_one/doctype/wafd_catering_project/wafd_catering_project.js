frappe.ui.form.on("WAFD Catering Project", {
    refresh(frm) {
        if (frm.is_new()) return;

        frm.add_custom_button(__("Generate Operation Plan"), () => {
            frappe.confirm(
                __("Create meal plans, production batches and delivery trips for this project?"),
                () => frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project.generate_operation_plan",
                    args: { project_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Generating operation plan..."),
                    callback(r) {
                        const result = r.message || {};
                        const totals = result.totals || {};
                        const warnings = (result.warnings || []).map(x => `<li>${frappe.utils.escape_html(x)}</li>`).join("");
                        frappe.msgprint({
                            title: __("Operation Plan Created"),
                            indicator: warnings ? "orange" : "green",
                            message: `
                                <p>${__("Meal plans: {0} created, {1} existing.", [result.meal_plans_created || 0, result.meal_plans_skipped || 0])}</p>
                                <p>${__("Production batches: {0} created, {1} existing.", [result.batches_created || 0, result.batches_skipped || 0])}</p>
                                <p>${__("Delivery trips: {0} created, {1} existing.", [result.trips_created || 0, result.trips_skipped || 0])}</p>
                                <p><b>${__("Current totals")}</b>: ${totals.meal_plans || 0} / ${totals.production_batches || 0} / ${totals.delivery_trips || 0}</p>
                                ${warnings ? `<hr><ul>${warnings}</ul>` : ""}
                            `
                        });
                        frm.reload_doc();
                    }
                })
            );
        }, __("Operations"));

        frm.add_custom_button(__("Generate Meal Plans"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project.generate_meal_plans",
                args: { project_name: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating meal plans..."),
                callback(r) {
                    const result = r.message || {};
                    frappe.msgprint(__("Created {0} meal plans; skipped {1} existing plans.", [result.created || 0, result.skipped || 0]));
                }
            });
        }, __("Operations"));

        frm.add_custom_button(__("Meal Plan"), () => frappe.new_doc("WAFD Meal Plan", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Delivery Trip"), () => frappe.new_doc("WAFD Delivery Trip", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Project Cost"), () => frappe.new_doc("WAFD Project Cost", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Project Revenue"), () => frappe.new_doc("WAFD Project Revenue", { project: frm.doc.name }), __("Create"));
    },
    contract(frm) {
        if (!frm.doc.contract) return;
        frappe.db.get_value("WAFD Contract", frm.doc.contract, [
            "mission", "start_date", "end_date", "beneficiary_count", "contract_value", "currency"
        ]).then(r => {
            const values = r.message || {};
            Object.keys(values).forEach(fieldname => {
                if (!frm.doc[fieldname] && values[fieldname] !== undefined && values[fieldname] !== null) {
                    frm.set_value(fieldname, values[fieldname]);
                }
            });
        });
    }
});

frappe.ui.form.on("WAFD Project Service", {
    service_start_date: recalculate,
    service_end_date: recalculate,
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
