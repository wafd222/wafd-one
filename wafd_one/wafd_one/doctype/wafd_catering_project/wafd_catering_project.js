frappe.ui.form.on("WAFD Catering Project", {
    refresh(frm) {
        if (frm.is_new()) return;

        frm.add_custom_button(__("Generate Operation Plan"), () => {
            frappe.confirm(
                __("Create meal plans and production batches for this project? Delivery trips are created after loading."),
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
                                <p>${__("Delivery trips are created after loading. Existing trips: {0}.", [result.trips_skipped || 0])}</p>
                                <p><b>${__("Current totals")}</b>: ${totals.meal_plans || 0} / ${totals.production_batches || 0} / ${totals.delivery_trips || 0}</p>
                                ${warnings ? `<hr><ul>${warnings}</ul>` : ""}
                            `
                        });
                        frm.reload_doc();
                    }
                })
            );
        }, __("Operations"));

        frm.add_custom_button(__("Refresh Production Materials"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project.refresh_production_materials",
                args: { project_name: frm.doc.name },
                freeze: true, freeze_message: __("Calculating production materials..."),
                callback(r) {
                    const x = r.message || {};
                    frappe.msgprint(__("Batches: {0}<br>Materials available: {1}<br>Shortages: {2}<br>Total material cost: {3}", [x.batches || 0, x.available || 0, x.shortage || 0, format_currency(x.material_cost || 0)]));
                }
            });
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

frappe.ui.form.on("WAFD Catering Project", {refresh(frm){if(!frm.is_new()){frm.add_custom_button(__("إنشاء فاتورة من التسليم"),()=>{frappe.call({method:"wafd_one.finance.create_invoice_from_deliveries",args:{project_name:frm.doc.name},freeze:true,callback:r=>{if(r.message) frappe.set_route("Form","WAFD Invoice",r.message);}});},__("المالية"));frm.add_custom_button(__("تحديث الربحية"),()=>frappe.call({method:"wafd_one.finance.refresh_project_financials",args:{project_name:frm.doc.name},callback:()=>frm.reload_doc()}),__("المالية"));}}});

frappe.ui.form.on("WAFD Catering Project", {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__("Operations Summary"), () => {
            frappe.call({
                method: "wafd_one.operations.get_project_operations_summary",
                args: { project_name: frm.doc.name },
                callback(r) {
                    const x = r.message || {};
                    frappe.msgprint({
                        title: __("Operations Summary"),
                        message: `
                            <p>${__("Meal Plans")}: <b>${x.meal_plans || 0}</b></p>
                            <p>${__("Production Batches")}: <b>${x.production_batches || 0}</b></p>
                            <p>${__("Packaging Records")}: <b>${x.packaging_records || 0}</b></p>
                            <p>${__("Loading Records")}: <b>${x.loading_records || 0}</b></p>
                            <p>${__("Delivery Trips")}: <b>${x.delivery_trips || 0}</b></p>
                            <p>${__("Delivery Proofs")}: <b>${x.delivery_proofs || 0}</b></p>
                            <p>${__("Invoices")}: <b>${x.invoices || 0}</b></p>
                            <p>${__("Progress")}: <b>${flt(x.progress_percent || 0).toFixed(1)}%</b></p>`
                    });
                }
            });
        }, __("Operations"));
    }
});
