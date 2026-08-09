frappe.ui.form.on("WAFD Daily Meal Plan", {
    setup(frm) {
        frm.set_query("warehouse", "source_warehouses", () => ({ filters: { status: "نشط / Active" } }));
    },
    onload(frm) {
        if (frm.is_new() && frm.doc.project) load_project_defaults(frm, false);
    },
    refresh(frm) {
        frm.toggle_display("source_warehouse", false);
        if (frm.is_new()) {
            if (frm.doc.project) load_project_defaults(frm, false);
            frm.add_custom_button(__("تحميل وجبات العقد / Load Contract Meals"), () => {
                load_project_defaults(frm, true);
            }, __("Operations"));
            return;
        }
        if (!frm.doc.missing_recipe_count) {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_daily_meal_plan.wafd_daily_meal_plan.get_existing_production_batches",
                args: { daily_plan_name: frm.doc.name },
                callback(r) {
                    const rows = r.message || [];
                    if (rows.length) {
                        frm.add_custom_button(__("فتح دفعة الإنتاج / Open Production Batch"), () => {
                            frappe.set_route("Form", "WAFD Production Batch", rows[0]);
                        }, __("Operations"));
                    } else if (frm.doc.status !== "تم التسليم / Delivered") {
                        frm.add_custom_button(__("Create Production Batches"), () => {
                            frappe.confirm(__("Create one production batch for every meal and copy all source warehouses?"), () => {
                                frappe.call({
                                    method: "wafd_one.wafd_one.doctype.wafd_daily_meal_plan.wafd_daily_meal_plan.create_production_batches",
                                    args: { daily_plan_name: frm.doc.name }, freeze: true,
                                    freeze_message: __("Creating production batches..."),
                                    callback(xr) {
                                        const x = xr.message || {};
                                        if ((x.batch_names || []).length) frappe.set_route("Form", "WAFD Production Batch", x.batch_names[0]);
                                        else frm.reload_doc();
                                    }
                                });
                            });
                        }, __("Operations"));
                    }
                }
            });
        }
    },
    project(frm) {
        if (!frm.doc.project) return;
        load_project_defaults(frm, true);
    },
    service_date(frm) {
        if (!frm.doc.project || !frm.doc.service_date) return;
        if (!frm.doc.meals || !frm.doc.meals.length) load_project_defaults(frm, false);
    }
});

function load_project_defaults(frm, force_meals) {
    if (!frm.doc.project || frm.__loading_project_defaults) return;
    frm.__loading_project_defaults = true;
    frappe.call({
        method: "wafd_one.wafd_one.doctype.wafd_daily_meal_plan.wafd_daily_meal_plan.get_project_plan_defaults",
        args: { project_name: frm.doc.project, service_date: frm.doc.service_date || null },
        freeze: !!force_meals,
        freeze_message: __("Loading all contract meals..."),
        callback(r) {
            const x = r.message || {};
            const assignments = [];
            if (!frm.doc.hotel && x.hotel) assignments.push(frm.set_value("hotel", x.hotel));
            if (x.service_date && (!frm.doc.service_date || x.requested_date_adjusted)) {
                assignments.push(frm.set_value("service_date", x.service_date));
            }
            if (!frm.doc.plan_title && x.plan_title) assignments.push(frm.set_value("plan_title", x.plan_title));
            if (!frm.doc.kitchen && x.kitchen) assignments.push(frm.set_value("kitchen", x.kitchen));

            const shouldLoadMeals = force_meals || !frm.doc.meals || !frm.doc.meals.length;
            if (shouldLoadMeals && (x.meals || []).length) {
                frm.clear_table("meals");
                (x.meals || []).forEach(item => {
                    const row = frm.add_child("meals");
                    Object.assign(row, item);
                });
                frm.refresh_field("meals");
            }

            const validSources = (frm.doc.source_warehouses || []).filter(row => row.warehouse);
            if (validSources.length !== (frm.doc.source_warehouses || []).length) {
                frm.clear_table("source_warehouses");
                validSources.forEach(item => {
                    const row = frm.add_child("source_warehouses");
                    Object.assign(row, item);
                });
                frm.refresh_field("source_warehouses");
            }
            const shouldLoadSources = force_meals || !validSources.length;
            if (shouldLoadSources && (x.source_warehouses || []).length) {
                frm.clear_table("source_warehouses");
                (x.source_warehouses || []).forEach(item => {
                    const row = frm.add_child("source_warehouses");
                    Object.assign(row, item);
                });
                frm.refresh_field("source_warehouses");
            }
            if ((!frm.doc.source_warehouses || !frm.doc.source_warehouses.length) && x.source_warehouse) {
                const row = frm.add_child("source_warehouses");
                row.warehouse = x.source_warehouse; row.priority = 1; row.is_default = 1;
                frm.refresh_field("source_warehouses");
            }
            Promise.all(assignments).then(() => {
                if (frm.doc.service_date && x.hotel && (!frm.doc.plan_title || force_meals)) {
                    frm.set_value("plan_title", x.plan_title || `${frm.doc.project} - ${x.hotel} - ${frm.doc.service_date}`);
                }
            });
            if (x.requested_date_adjusted) {
                frappe.show_alert({ message: __(`Service date adjusted to ${x.service_date}`), indicator: "orange" });
            }
            if (shouldLoadMeals && !(x.meals || []).length) {
                frappe.msgprint(__("No contract meals are available. Check the linked contract services."));
            } else if (force_meals) {
                frappe.show_alert({ message: __(`${(x.meals || []).length} contract meals loaded`), indicator: "green" });
            }
        },
        always() { frm.__loading_project_defaults = false; }
    });
}

frappe.ui.form.on("WAFD Source Warehouse Row", {
    is_default(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.is_default) return;
        (frm.doc.source_warehouses || []).forEach(other => {
            if (other.name !== row.name && other.is_default) frappe.model.set_value(other.doctype, other.name, "is_default", 0);
        });
    }
});

frappe.ui.form.on("WAFD Daily Meal Plan Item", {
    quantity: calculate_row, unit_price: calculate_row, estimated_unit_cost: calculate_row,
    recipe(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.recipe) return;
        frappe.db.get_value("WAFD Recipe", row.recipe, ["cost_per_portion", "recipe_name"]).then(r => {
            if (!r.message) return;
            frappe.model.set_value(cdt, cdn, "estimated_unit_cost", r.message.cost_per_portion || 0);
            if (!row.menu_name) frappe.model.set_value(cdt, cdn, "menu_name", r.message.recipe_name || "");
        });
    }
});

function calculate_row(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const value = flt(row.quantity) * flt(row.unit_price);
    const cost = flt(row.quantity) * flt(row.estimated_unit_cost);
    frappe.model.set_value(cdt, cdn, "total_value", value);
    frappe.model.set_value(cdt, cdn, "estimated_cost", cost);
    frappe.model.set_value(cdt, cdn, "estimated_profit", value - cost);
    frappe.model.set_value(cdt, cdn, "estimated_margin_percent", value ? ((value - cost) / value) * 100 : 0);
}
