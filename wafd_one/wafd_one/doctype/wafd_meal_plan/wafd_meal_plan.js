frappe.ui.form.on("WAFD Meal Plan", {
    setup(frm) {
        frm.set_query("hotel", () => ({ filters: frm.doc.project ? { mission: frm.doc.__onload?.mission } : {} }));
    },
    project(frm) {
        if (!frm.doc.project) return;
        frappe.db.get_value("WAFD Catering Project", frm.doc.project, ["mission", "start_date", "end_date"]).then(r => {
            frm.doc.__onload = r.message || {};
            frm.set_query("hotel", () => ({ filters: { mission: r.message.mission } }));
        });
    },
    recipe(frm) {
        if (!frm.doc.recipe) return;
        frappe.db.get_value("WAFD Recipe", frm.doc.recipe, ["cost_per_portion", "recipe_name"]).then(r => {
            if (!r.message) return;
            frm.set_value("estimated_unit_cost", r.message.cost_per_portion || 0);
            if (!frm.doc.menu_name) frm.set_value("menu_name", r.message.recipe_name);
        });
    },
    quantity: calculate_totals,
    unit_price: calculate_totals,
    estimated_unit_cost: calculate_totals
});

function calculate_totals(frm) {
    const value = flt(frm.doc.quantity) * flt(frm.doc.unit_price);
    const cost = flt(frm.doc.quantity) * flt(frm.doc.estimated_unit_cost);
    frm.set_value("total_value", value);
    frm.set_value("estimated_cost", cost);
    frm.set_value("estimated_profit", value - cost);
    frm.set_value("estimated_margin_percent", value ? ((value - cost) / value) * 100 : 0);
}
