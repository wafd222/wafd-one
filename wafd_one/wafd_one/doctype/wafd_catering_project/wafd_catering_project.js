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

        frm.add_custom_button(__("إنشاء خطط الوجبات تلقائياً / Generate Meal Plans"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project.get_meal_plan_preview",
                args: { project_name: frm.doc.name },
                freeze: true,
                freeze_message: __("Preparing meal schedule preview..."),
                callback(r) {
                    const x = r.message || {};
                    const source = x.derived_from_services
                        ? __("Project service rows")
                        : __("Project dates and first/last meal");
                    const message = `
                        <p><b>${__("Source")}</b>: ${source}</p>
                        <p>${__("Days")}: <b>${x.day_count || 0}</b></p>
                        <p>${__("Hotels")}: <b>${x.hotel_count || 0}</b></p>
                        <p>${__("Meal-plan records")}: <b>${x.plan_count || 0}</b></p>
                        <p>${__("Total planned meals")}: <b>${format_number(x.total_quantity || 0)}</b></p>
                        <p>${__("Continue and create only missing plans?")}</p>`;
                    frappe.confirm(message, () => generate_meal_plans(frm));
                }
            });
        }, __("Operations"));

        if ((frm.doc.meal_plans_created || 0) > 0 || frm.doc.status !== "مسودة / Draft") {
            frm.add_custom_button(__("خطة وجبة يدوية / Manual Meal Plan"), () =>
                frappe.new_doc("WAFD Meal Plan", { project: frm.doc.name }), __("Create"));
        }
        frm.add_custom_button(__("Delivery Trip"), () => frappe.new_doc("WAFD Delivery Trip", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Project Cost"), () => frappe.new_doc("WAFD Project Cost", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Project Revenue"), () => frappe.new_doc("WAFD Project Revenue", { project: frm.doc.name }), __("Create"));
    },
    contract(frm) {
        if (!frm.doc.contract) return;
        frappe.db.get_value("WAFD Contract", frm.doc.contract, [
            "mission", "hotel", "start_date", "end_date", "beneficiary_count", "contract_value", "currency"
        ]).then(r => {
            const values = r.message || {};
            Object.keys(values).forEach(fieldname => {
                if (fieldname === "hotel") return;
                if (!frm.doc[fieldname] && values[fieldname] !== undefined && values[fieldname] !== null) {
                    frm.set_value(fieldname, values[fieldname]);
                }
            });
            if (values.hotel && !frm.doc.primary_hotel) {
                frm.set_value("primary_hotel", values.hotel);
            }
            if (values.hotel && !(frm.doc.hotels || []).some(row => row.hotel === values.hotel)) {
                const row = frm.add_child("hotels");
                row.hotel = values.hotel;
                row.guest_count = frm.doc.beneficiary_count || values.beneficiary_count || 0;
                frm.refresh_field("hotels");
            }
        });
    }
});

function generate_meal_plans(frm) {
    frappe.call({
        method: "wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project.generate_meal_plans",
        args: { project_name: frm.doc.name },
        freeze: true,
        freeze_message: __("Generating meal plans..."),
        callback(r) {
            const result = r.message || {};
            const totals = result.totals || {};
            const warnings = (result.warnings || []).slice(0, 10)
                .map(x => `<li>${frappe.utils.escape_html(x)}</li>`).join("");
            frappe.msgprint({
                title: __("Meal Plans Generated"),
                indicator: warnings ? "orange" : "green",
                message: `
                    <p>${__("Created records")}: <b>${result.created || 0}</b></p>
                    <p>${__("Skipped existing records")}: <b>${result.skipped || 0}</b></p>
                    <p>${__("Current plan records")}: <b>${totals.meal_plans || 0}</b></p>
                    <p>${__("Current planned meals")}: <b>${format_number(totals.total_quantity || 0)}</b></p>
                    ${warnings ? `<hr><p><b>${__("Recipes still required before production")}</b></p><ul>${warnings}</ul>` : ""}`
            });
            frm.reload_doc();
        }
    });
}

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

frappe.ui.form.on("WAFD Catering Project", {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__("تعهد فندق"), () => {
            frappe.new_doc("WAFD Hotel Undertaking", {
                project: frm.doc.name,
                contract: frm.doc.contract,
                mission: frm.doc.mission,
                hotel: frm.doc.primary_hotel,
                beneficiary_count: frm.doc.beneficiary_count,
                start_date: frm.doc.start_date,
                end_date: frm.doc.end_date
            });
        }, __("المستندات"));
    }
});


frappe.ui.form.on("WAFD Catering Project", {
    refresh(frm) {
        if (frm.is_new()) return;

        frm.add_custom_button(__("Financial Status"), () => {
            frappe.call({
                method: "wafd_one.finance.get_project_billing_status",
                args: { project_name: frm.doc.name },
                freeze: true,
                callback(r) {
                    const x = r.message || {};
                    frappe.msgprint({
                        title: __("Financial Status"),
                        indicator: x.ready_for_closure ? "green" : "orange",
                        message: `
                            <p>${__("Delivered Meals")}: <b>${format_number(x.delivered_meals || 0)}</b> / ${format_number(x.total_meals || 0)}</p>
                            <p>${__("Uninvoiced Delivered Quantity")}: <b>${format_number(x.billable_quantity || 0)}</b></p>
                            <p>${__("Invoices")}: <b>${x.invoice_count || 0}</b></p>
                            <p>${__("Invoiced Amount")}: <b>${format_currency(x.invoiced_amount || 0)}</b></p>
                            <p>${__("Collected Revenue")}: <b>${format_currency(x.revenue || 0)}</b></p>
                            <p>${__("Outstanding Amount")}: <b>${format_currency(x.outstanding_amount || 0)}</b></p>
                            <p>${__("Profit")}: <b>${format_currency(x.profit || 0)}</b></p>
                            <p><b>${x.ready_for_closure ? __("Ready for financial closure") : __("Financial closure requirements are not complete")}</b></p>`
                    });
                }
            });
        }, __("Finance"));

        if (frm.doc.status !== "مكتمل / Completed" && frm.doc.status !== "ملغي / Cancelled") {
            frm.add_custom_button(__("Close Project Financially"), () => {
                frappe.confirm(
                    __("Complete this project only after all deliveries, invoices and collections are closed?"),
                    () => frappe.call({
                        method: "wafd_one.finance.close_project_financially",
                        args: { project_name: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Checking financial closure..."),
                        callback(r) {
                            if (r.message) {
                                frappe.show_alert({ message: __("Project closed successfully"), indicator: "green" });
                                frm.reload_doc();
                            }
                        }
                    })
                );
            }, __("Finance"));
        }
    }
});
