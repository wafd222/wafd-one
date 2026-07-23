frappe.ui.form.on("WAFD Daily Meal Plan", {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__("Create Production Batches"), () => {
            frappe.confirm(__("Create one production batch for every meal in this daily plan?"), () => {
                frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_daily_meal_plan.wafd_daily_meal_plan.create_production_batches",
                    args: { daily_plan_name: frm.doc.name },
                    freeze: true,
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
});

frappe.ui.form.on("WAFD Daily Meal Plan Item", {
    quantity: calculate_row,
    unit_price: calculate_row,
    estimated_unit_cost: calculate_row,
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
