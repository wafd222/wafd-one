frappe.ui.form.on("WAFD Catering Project", {
    refresh(frm) {
        frm.set_query("contract", () => ({ filters: { project: ["in", [frm.doc.name, ""]] } }));
        if (!frm.is_new()) {
            frm.add_custom_button(__("Meal Plan"), () => frappe.new_doc("WAFD Meal Plan", { project: frm.doc.name }));
            frm.add_custom_button(__("Delivery Trip"), () => frappe.new_doc("WAFD Delivery Trip", { project: frm.doc.name }));
            frm.add_custom_button(__("Project Cost"), () => frappe.new_doc("WAFD Project Cost", { project: frm.doc.name }), __("Create"));
            frm.add_custom_button(__("Project Revenue"), () => frappe.new_doc("WAFD Project Revenue", { project: frm.doc.name }), __("Create"));
        }
        frm.dashboard.set_headline_alert(__("Planned meals: {0} | Delivered: {1} | Progress: {2}%", [frm.doc.total_meals || 0, frm.doc.delivered_meals || 0, frm.doc.progress_percent || 0]));
    },
    contract(frm) {
        if (!frm.doc.contract) return;
        frappe.db.get_value("WAFD Contract", frm.doc.contract, ["contract_value", "start_date", "end_date"]).then(r => {
            const v = r.message || {};
            frm.set_value("contract_value", v.contract_value || frm.doc.contract_value);
            frm.set_value("start_date", v.start_date || frm.doc.start_date);
            frm.set_value("end_date", v.end_date || frm.doc.end_date);
        });
    }
});

frappe.ui.form.on("WAFD Project Service", {
    meals_per_day: calculate_service, service_days: calculate_service, unit_price: calculate_service,
    start_date: calculate_days, end_date: calculate_days
});

function calculate_days(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.start_date && row.end_date) {
        const days = frappe.datetime.get_day_diff(row.end_date, row.start_date) + 1;
        frappe.model.set_value(cdt, cdn, "service_days", Math.max(days, 0));
    }
    calculate_service(frm, cdt, cdn);
}
function calculate_service(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const total = (row.meals_per_day || 0) * (row.service_days || 0);
    frappe.model.set_value(cdt, cdn, "total_meals", total);
    frappe.model.set_value(cdt, cdn, "total_value", total * (row.unit_price || 0));
}
