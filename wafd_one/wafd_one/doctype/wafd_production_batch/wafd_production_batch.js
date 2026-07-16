frappe.ui.form.on("WAFD Production Batch", {
    refresh(frm) {
        if (frm.is_new()) return;

        frm.add_custom_button(__("Create Material Issue"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.create_material_issue",
                args: { batch_name: frm.doc.name },
                freeze: true,
                freeze_message: __("Preparing material issue..."),
                callback(r) {
                    if (!r.message) return;
                    frm.reload_doc();
                    frappe.set_route("Form", "WAFD Stock Movement", r.message.name);
                }
            });
        }, __("Operations"));

        frm.add_custom_button(__("Quality Inspection"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.create_quality_inspection",
                args: { batch_name: frm.doc.name },
                callback(r) {
                    if (r.message) frappe.set_route("Form", "WAFD Quality Inspection", r.message.name);
                }
            });
        }, __("Operations"));
    },

    meal_plan(frm) {
        if (!frm.doc.meal_plan) return;
        frappe.db.get_value("WAFD Meal Plan", frm.doc.meal_plan, ["project", "recipe", "quantity"]).then(r => {
            if (!r.message) return;
            frm.set_value("project", r.message.project);
            frm.set_value("recipe", r.message.recipe);
            frm.set_value("planned_quantity", r.message.quantity);
        });
    }
});
