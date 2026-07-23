frappe.ui.form.on("WAFD Daily Meal Plan", {
    setup(frm) {
        frm.set_query("warehouse", "source_warehouses", () => ({ filters: { status: "نشط / Active" } }));
    },
    refresh(frm) {
        frm.toggle_display("source_warehouse", false);
        if (frm.is_new()) {
            load_project_defaults(frm);
            return;
        }
        if (!frm.doc.missing_recipe_count && frm.doc.status !== "تم التسليم / Delivered") {
            frm.add_custom_button(__("Create Production Batches"), () => {
                frappe.confirm(__("Create one production batch for every meal and copy all source warehouses?"), () => {
                    frappe.call({
                        method: "wafd_one.wafd_one.doctype.wafd_daily_meal_plan.wafd_daily_meal_plan.create_production_batches",
                        args: { daily_plan_name: frm.doc.name }, freeze: true,
                        freeze_message: __("Creating production batches..."),
                        callback(r) {
                            const x = r.message || {};
                            frappe.msgprint(`${__("Created")}: ${x.created || 0}<br>${__("Existing")}: ${x.skipped || 0}`);
                            frm.reload_doc();
                        }
                    });
                });
            }, __("Operations"));
        }
    },
    project(frm) { load_project_defaults(frm); }
});

function load_project_defaults(frm) {
    if (!frm.doc.project) return;
    frappe.db.get_value("WAFD Catering Project", frm.doc.project, ["primary_hotel", "default_kitchen", "default_source_warehouse"]).then(r => {
        const x = r.message || {};
        if (!frm.doc.hotel && x.primary_hotel) frm.set_value("hotel", x.primary_hotel);
        if (!frm.doc.kitchen && x.default_kitchen) frm.set_value("kitchen", x.default_kitchen);
        if ((!frm.doc.source_warehouses || !frm.doc.source_warehouses.length) && x.default_source_warehouse) {
            const row = frm.add_child("source_warehouses");
            row.warehouse = x.default_source_warehouse; row.priority = 1; row.is_default = 1;
            frm.refresh_field("source_warehouses");
        }
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
